import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from models import ChatResponse, SourceResponse
from retrieval.reranker import CrossEncoderReranker

from config import (
    CHAT_MODEL,
    CHROMA_PATH,
    MAX_CHUNK_SIZE,
    COLLECTION_NAME,
    EMBED_MODEL,
    OLLAMA_HOST,
    MIN_CHUNK_SIZE,
    SIMILARITY_THRESHOLD,
    RERANK_MODEL,
    RETRIEVAL_TOP_K,
    FINAL_TOP_K
)
from retrieval.vector_search import VectorSearch
from retrieval.keyword_search import KeywordSearch
from embedder import Embedder
from generator import Generator
from ingestion import Ingestion
from pipeline import Pipeline
from retrieval.retriever import Retriever
from vector_store import VectorStore
from chunking import SemanticChunker
from retrieval.fusion import ReciprocalRankFusion

logger = logging.getLogger(__name__)

app = FastAPI()


class ChatRequest(BaseModel):
    question: str


vector_store = VectorStore(
    path=CHROMA_PATH,
    collection_name=COLLECTION_NAME,
)

embedder = Embedder(
    model=EMBED_MODEL,
    host=OLLAMA_HOST,
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
    model=CHAT_MODEL,
    host=OLLAMA_HOST,
)

pipeline = Pipeline(
    embedder=embedder,
    retriever=retriever,
    generator=generator,
)

chunker = SemanticChunker(
    embedder=embedder,
    max_chunk_size=MAX_CHUNK_SIZE,
    min_chunk_size=MIN_CHUNK_SIZE,
    similarity_threshold=SIMILARITY_THRESHOLD,
)

ingestion = Ingestion(
    keyword_search=keyword_search,
    embedder=embedder,
    vector_store=vector_store,
    chunker=chunker,
)


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict[str, str]:
    file_path = file.filename

    logger.info("Uploading document: %s", file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        ingestion.ingest(file_path)
    except Exception as e:
        logger.exception("Failed to index document: %s", file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index document: {e}",
        )

    logger.info("Document indexed successfully: %s", file.filename)

    return {
        "message": "Document indexed successfully."
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Generate an answer for the given question using the RAG pipeline.
    """

    try:
        result = pipeline.run(request.question)

        return ChatResponse(
            answer=result.answer,
            sources=[
                SourceResponse(
                    source=chunk.metadata.source,
                    page=chunk.metadata.page,
                    chunk=chunk.metadata.chunk,
                    heading=chunk.metadata.heading,
                    preview=(
                        chunk.document.removeprefix(
                            f"{chunk.metadata.heading}\n\n"
                        )[:200]
                        if chunk.metadata.heading
                        else chunk.document[:200]
                    ),
                )
                for chunk in result.chunks
            ],
        )

    except Exception as e:
        logger.exception("Failed to generate response")
        raise HTTPException(status_code=500, detail=str(e))

