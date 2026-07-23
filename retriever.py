from models import RetrievedChunk
from vector_store import VectorStore


class Retriever:
    """
    Retrieves the most relevant document chunks from the vector store.
    """

    def __init__(self, vector_store: VectorStore, top_k: int = 3):
        self.vector_store = vector_store
        self.top_k = top_k

    def search(self, embedding: list[float]) -> list[RetrievedChunk]:
        """
        Search for the most relevant unique chunks for the given embedding.
        """
        chunks = self.vector_store.query(
            embedding=embedding,
            top_k=self.top_k,
        )

        return self._deduplicate(chunks)

    def _deduplicate(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Remove duplicate chunks while preserving retrieval order.
        """
        seen: set[tuple[str, int, int]] = set()
        unique_chunks: list[RetrievedChunk] = []

        for chunk in chunks:
            key = (
                chunk.metadata.source,
                chunk.metadata.page,
                chunk.metadata.chunk,
            )

            if key not in seen:
                seen.add(key)
                unique_chunks.append(chunk)

        return unique_chunks