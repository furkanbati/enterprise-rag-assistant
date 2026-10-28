import json
import logging
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from models import ChatResponse, SourceResponse
from retrieval.reranker import CrossEncoderReranker

from config import (
    CHAT_MODEL,
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
    RETRIEVAL_TOP_K,
    FINAL_TOP_K
)
from retrieval.vector_search import VectorSearch
from retrieval.keyword_search import KeywordSearch
from generator import Generator
from document_parser import SUPPORTED_EXTENSIONS
from ingestion import Ingestion
from pipeline import Pipeline
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


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """
    Stream the answer as newline-delimited JSON events: the sources once
    retrieval is done, then the answer tokens, then a final "done" event
    with timings, or an "error" event if anything fails.
    """

    return StreamingResponse(
        _stream_events(request.question),
        media_type="application/x-ndjson",
    )


def _stream_events(question: str) -> Iterator[str]:
    try:
        started = time.perf_counter()
        chunks = pipeline.retrieve(question)
        retrieval_ms = (time.perf_counter() - started) * 1000

        yield _event({
            "type": "sources",
            "sources": [
                _source_response(chunk).model_dump()
                for chunk in chunks
            ],
        })

        started = time.perf_counter()

        for text in pipeline.stream(question, chunks):
            yield _event({"type": "token", "text": text})

        yield _event({
            "type": "done",
            "retrieval_ms": round(retrieval_ms),
            "generation_ms": round((time.perf_counter() - started) * 1000),
        })

    except Exception as e:
        logger.exception("Failed to stream response")
        yield _event({"type": "error", "detail": str(e)})


def _documents() -> list[dict]:
    return [
        {"source": source, "chunks": chunks}
        for source, chunks in sorted(vector_store.list_sources().items())
    ]


def _event(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False) + "\n"


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
