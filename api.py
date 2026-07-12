
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from config import (
    CHAT_MODEL,
    CHROMA_PATH,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBED_MODEL,
    OLLAMA_HOST,
    OVERLAP,
)
from embedder import Embedder
from generator import Generator
from ingestion import Ingestion
from pipeline import Pipeline
from retriever import Retriever
from vector_store import VectorStore


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
async def upload(file: UploadFile = File(...)):
    file_path = file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    ingestion.ingest(file_path)

    return {
        "message": "Document indexed successfully."
    }


@app.post("/chat")
def chat(request: ChatRequest):
    answer = pipeline.run(request.question)

    return {
        "answer": answer,
    }

