from models import RetrievedChunk
from vector_store import VectorStore


class VectorSearch:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(
        self,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        return self.vector_store.query(
            embedding=embedding,
            top_k=top_k,
        )