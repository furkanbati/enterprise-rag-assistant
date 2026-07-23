import logging

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from models import ChatResponse, SourceResponse
from config import (
    CHAT_MODEL,
    CHROMA_PATH,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBED_MODEL,
    OLLAMA_HOST,
    OVERLAP,
    TOP_K,
    MAX_DISTANCE
)
from embedder import Embedder
from generator import Generator
from ingestion import Ingestion
from pipeline import Pipeline
from retriever import Retriever
from vector_store import VectorStore

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

retriever = Retriever(
    vector_store=vector_store,
    top_k=TOP_K,
    max_distance=MAX_DISTANCE
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

ingestion = Ingestion(
    embedder=embedder,
    vector_store=vector_store,
    chunk_size=CHUNK_SIZE,
    overlap=OVERLAP,
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
                    distance=chunk.distance,
                )
                for chunk in result.chunks
            ],
        )

    except Exception as e:
        logger.exception("Failed to generate response")
        raise HTTPException(status_code=500, detail=str(e))

