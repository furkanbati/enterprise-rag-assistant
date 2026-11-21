import json
import logging
import tempfile
import time
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool
from pydantic import BaseModel
from models import ChatResponse, SourceResponse
from retrieval.reranker import CrossEncoderReranker

from config import (
    CHAT_MODEL,
    CHAT_MODEL_TR,
    CHROMA_PATH,
    CHUNK_CONTEXT,
    CHUNKING_STRATEGY,
    MAX_CHUNK_SIZE,
    COLLECTION_NAME,
    EMBED_MODEL,
    EMBED_PROVIDER,
    LLM_PROVIDER,
    MIN_CHUNK_SIZE,
    OCR_ENGINE,
    SEMANTIC_PERCENTILE,
    SEMANTIC_WINDOW,
    RERANK_MODEL,
    RERANK_MODEL_TR,
    RETRIEVAL_TOP_K,
    FINAL_TOP_K
)
from retrieval.vector_search import VectorSearch
from retrieval.keyword_search import KeywordSearch
from generator import Generator
from document_parser import SUPPORTED_EXTENSIONS
from ingestion import Ingestion
from pipeline import Pipeline
from providers.base import close_stream
from providers.factory import build_chat_client, build_embedder
from retrieval.retriever import Retriever
from vector_store import VectorStore, collection_name_for
from chunking import build_chunker, chunking_id, strip_context
from retrieval.fusion import ReciprocalRankFusion

logger = logging.getLogger(__name__)

app = FastAPI()


class ChatRequest(BaseModel):
    question: str


vector_store = VectorStore(
    path=CHROMA_PATH,
    collection_name=collection_name_for(
        COLLECTION_NAME,
        EMBED_PROVIDER,
        EMBED_MODEL,
        chunking_id(
            CHUNKING_STRATEGY,
            SEMANTIC_PERCENTILE,
            SEMANTIC_WINDOW,
            CHUNK_CONTEXT,
        ),
    ),
    embedding_model=f"{EMBED_PROVIDER}/{EMBED_MODEL}",
)

embedder = build_embedder(
    provider=EMBED_PROVIDER,
    model=EMBED_MODEL,
)

vector_search = VectorSearch(
    vector_store=vector_store,
)

keyword_search = KeywordSearch(vector_store)
keyword_search.rebuild()

fusion = ReciprocalRankFusion()

reranker = CrossEncoderReranker(RERANK_MODEL)

retriever = Retriever(
    vector_search=vector_search,
    keyword_search=keyword_search,
    fusion=fusion,
    reranker=reranker,
    retrieval_top_k=RETRIEVAL_TOP_K,
    final_top_k=FINAL_TOP_K,
    # Turkish questions get their own reranker only when it differs.
    language_rerankers=(
        {"tr": CrossEncoderReranker(RERANK_MODEL_TR)}
        if RERANK_MODEL_TR != RERANK_MODEL
        else None
    ),
)

generator = Generator(
    client=build_chat_client(
        provider=LLM_PROVIDER,
        model=CHAT_MODEL,
    ),
)

pipeline = Pipeline(
    embedder=embedder,
    retriever=retriever,
    generator=generator,
    language_generators=(
        {"tr": Generator(client=build_chat_client(provider=LLM_PROVIDER, model=CHAT_MODEL_TR))}
        if CHAT_MODEL_TR != CHAT_MODEL
        else None
    ),
)

chunker = build_chunker(
    strategy=CHUNKING_STRATEGY,
    embedder=embedder,
    max_chunk_size=MAX_CHUNK_SIZE,
    min_chunk_size=MIN_CHUNK_SIZE,
    breakpoint_percentile=SEMANTIC_PERCENTILE,
    window=SEMANTIC_WINDOW,
    include_title=CHUNK_CONTEXT,
)

ingestion = Ingestion(
    keyword_search=keyword_search,
    embedder=embedder,
    vector_store=vector_store,
    chunker=chunker,
    ocr_engine=OCR_ENGINE,
)


@app.get("/info")
def info() -> dict:
    """Active models, chunking configuration and indexed documents."""

    return {
        "chat_model": f"{LLM_PROVIDER}/{CHAT_MODEL}",
        "embedding_model": f"{EMBED_PROVIDER}/{EMBED_MODEL}",
        "chunking": chunking_id(
            CHUNKING_STRATEGY,
            SEMANTIC_PERCENTILE,
            SEMANTIC_WINDOW,
            CHUNK_CONTEXT,
        ),
        "reranker": RERANK_MODEL,
        # What Turkish questions use; the same as above unless set apart.
        "turkish": {
            "chat_model": f"{LLM_PROVIDER}/{CHAT_MODEL_TR}",
            "reranker": RERANK_MODEL_TR,
        },
        "documents": _documents(),
    }


@app.get("/documents")
def documents() -> list[dict]:
    """Indexed documents and their number of chunks."""

    return _documents()


@app.delete("/documents/{source}")
def delete_document(source: str) -> dict:
    """Remove a document and all of its chunks from the index."""

    deleted = vector_store.delete_source(source)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {source}",
        )

    keyword_search.rebuild()
    logger.info("Deleted document: %s (%d chunks)", source, deleted)

    return {"source": source, "deleted_chunks": deleted}


@app.post("/upload")
def upload(file: UploadFile = File(...)) -> dict:
    # Keep only the name, so a crafted file name cannot write elsewhere.
    filename = Path(file.filename or "").name

    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Supported types: "
                + ", ".join(SUPPORTED_EXTENSIONS)
            ),
        )

    logger.info("Uploading document: %s", filename)

    # The file is only needed while it is indexed; the chunks keep its name.
    with tempfile.TemporaryDirectory() as directory:
        file_path = Path(directory) / filename
        file_path.write_bytes(file.file.read())

        try:
            result = ingestion.ingest(str(file_path))
        except ValueError as e:
            # The document was read but contains no usable text.
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.exception("Failed to index document: %s", filename)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to index document: {e}",
            )

    logger.info("Document indexed successfully: %s", filename)

    return {
        "message": "Document indexed successfully.",
        "source": result.source,
        "chunks": result.chunks,
        "replaced": result.replaced,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Generate an answer for the given question using the RAG pipeline.
    """

    try:
        result = pipeline.run(request.question)

        return ChatResponse(
            answer=result.answer,
            sources=[_source_response(chunk) for chunk in result.chunks],
        )

    except Exception as e:
        logger.exception("Failed to generate response")
        raise HTTPException(status_code=500, detail=str(e))


# Keep proxies (nginx and others) from buffering the stream, which would
# deliver the answer in one piece at the end.
STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}


@app.post("/chat/stream")
def chat_stream(request: ChatRequest, http_request: Request) -> StreamingResponse:
    """
    Stream the answer as events: the sources once retrieval is done, then
    the answer tokens, then a final "done" event with timings, or an "error"
    event if anything fails.

    The events are newline-delimited JSON by default, or Server-Sent Events
    when the request accepts text/event-stream.
    """

    if accepts_event_stream(http_request.headers.get("accept", "")):
        format_event, media_type = _sse_event, "text/event-stream"
    else:
        format_event, media_type = _event, "application/x-ndjson"

    return StreamingResponse(
        close_when_done(_stream_events(request.question, format_event)),
        media_type=media_type,
        headers=STREAM_HEADERS,
    )


async def close_when_done(events: Iterator[str]) -> AsyncIterator[str]:
    """Run a blocking event generator in the thread pool and close it as soon
    as the response ends, whatever the reason.

    When the client disconnects, Starlette cancels the response but leaves a
    plain generator to the garbage collector, which on an idle server can
    take minutes; meanwhile the model keeps generating an answer nobody
    reads. Closing it here stops the model's stream right away."""

    try:
        async for event in iterate_in_threadpool(events):
            yield event
    finally:
        # The worker thread has returned by now (cancellation waits for it),
        # so the generator is not running and can be closed.
        close_stream(events)


def accepts_event_stream(accept: str) -> bool:
    """Whether an Accept header asks for text/event-stream (with a non-zero
    quality). Other values, including */*, keep the NDJSON default."""

    for media_range in accept.split(","):
        media_type, *params = [part.strip() for part in media_range.split(";")]

        if media_type.lower() != "text/event-stream":
            continue

        for param in params:
            name, _, value = param.partition("=")

            if name.strip().lower() == "q":
                try:
                    return float(value) > 0
                except ValueError:
                    return False

        return True

    return False


def _stream_events(
    question: str,
    format_event: Callable[[dict], str],
) -> Iterator[str]:
    tokens = None

    try:
        started = time.perf_counter()
        chunks = pipeline.retrieve(question)
        retrieval_ms = (time.perf_counter() - started) * 1000

        yield format_event({
            "type": "sources",
            "sources": [
                _source_response(chunk).model_dump()
                for chunk in chunks
            ],
        })

        started = time.perf_counter()
        first_token_ms = None
        tokens = pipeline.stream(question, chunks)

        for text in tokens:
            if first_token_ms is None:
                first_token_ms = (time.perf_counter() - started) * 1000

            yield format_event({"type": "token", "text": text})

        yield format_event({
            "type": "done",
            "retrieval_ms": round(retrieval_ms),
            "first_token_ms": (
                None if first_token_ms is None else round(first_token_ms)
            ),
            "generation_ms": round((time.perf_counter() - started) * 1000),
        })

    except Exception as e:
        logger.exception("Failed to stream response")
        yield format_event({"type": "error", "detail": str(e)})

    finally:
        # When the client disconnects, stop the model's stream right away.
        close_stream(tokens)


def _documents() -> list[dict]:
    return [
        {"source": source, "chunks": chunks}
        for source, chunks in sorted(vector_store.list_sources().items())
    ]


def _event(data: dict) -> str:
    """One NDJSON event: a JSON object on its own line."""

    return json.dumps(data, ensure_ascii=False) + "\n"


def _sse_event(data: dict) -> str:
    """One Server-Sent Event, named after the event type. The JSON is on a
    single line: json.dumps escapes newlines inside strings."""

    payload = json.dumps(data, ensure_ascii=False)

    return f"event: {data['type']}\ndata: {payload}\n\n"


def _source_response(chunk) -> SourceResponse:
    return SourceResponse(
        source=chunk.metadata.source,
        title=chunk.metadata.title,
        page=chunk.metadata.page,
        chunk=chunk.metadata.chunk,
        heading=chunk.metadata.heading,
        preview=strip_context(
            chunk.document,
            chunk.metadata.title,
            chunk.metadata.heading,
        )[:200],
    )
