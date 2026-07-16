from vector_store import VectorStore
from models import RetrievedChunk


class Retriever:
    """Retrieves the most relevant document chunks from the vector store."""

    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 3,
    ) -> None:
        self.vector_store = vector_store
        self.top_k = top_k

    def search(
        self,
        embedding: list[float],
    ) -> list[RetrievedChunk]:
        return self.vector_store.query(
            embedding=embedding,
            top_k=self.top_k,
        )