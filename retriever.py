from models import RetrievedChunk
from vector_store import VectorStore
import logging
logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves the most relevant document chunks from the vector store.
    """

    def __init__(self, vector_store: VectorStore, top_k: int , max_distance: float ):
        self.vector_store = vector_store
        self.top_k = top_k
        self.max_distance = max_distance

    def search(
        self,
        embedding: list[float],
    ) -> list[RetrievedChunk]:
        chunks = self.vector_store.query(
            embedding=embedding,
            top_k=self.top_k,
        )

        chunks = self._deduplicate(chunks)

        filtered_chunks = self._filter_by_distance(chunks)

        if filtered_chunks:
            return filtered_chunks

        logger.warning(
            "No chunks passed distance threshold %.2f. Returning best available chunk.",
            self.max_distance,
        )

        return chunks[:1]

    def _filter_by_distance(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Remove chunks whose retrieval distance exceeds the configured threshold.
        """

        return [
            chunk
            for chunk in chunks
            if chunk.distance <= self.max_distance
        ]

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