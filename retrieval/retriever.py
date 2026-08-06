from models import RetrievedChunk
from retrieval.vector_search import VectorSearch
from retrieval.keyword_search import KeywordSearch
from retrieval.fusion import ReciprocalRankFusion
import logging

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves the most relevant document chunks from the vector store.
    """

    def __init__(
        self,
        vector_search: VectorSearch,
        keyword_search: KeywordSearch,
        fusion: ReciprocalRankFusion,
        top_k: int,
        max_distance: float,
    ):
        self.vector_search = vector_search
        self.keyword_search = keyword_search
        self.fusion = fusion
        self.top_k = top_k
        self.max_distance = max_distance

    def search(
        self,
        query: str,
        embedding: list[float],
    ) -> list[RetrievedChunk]:

        vector_chunks = self.vector_search.search(
            embedding=embedding,
            top_k=self.top_k,
        )

        print("\n========== VECTOR RESULTS ==========")
        for chunk in vector_chunks:
            print(chunk)
        for chunk in vector_chunks:
            logger.info(
                "chunk=%s | vector=%s | keyword=%s | fusion=%s",
                chunk.metadata.chunk,
                chunk.vector_score,
                chunk.keyword_score,
                chunk.fusion_score,
            )

        keyword_chunks = self.keyword_search.search(
            query=query,
            top_k=self.top_k,
        )

        print("\n========== KEYWORD RESULTS ==========")
        for chunk in keyword_chunks:
            print(chunk)
        for chunk in keyword_chunks:
            logger.info(
                "chunk=%s | vector=%s | keyword=%s | fusion=%s",
                chunk.metadata.chunk,
                chunk.vector_score,
                chunk.keyword_score,
                chunk.fusion_score,
            )

        chunks = self.fusion.fuse(
            vector_chunks,
            keyword_chunks,
        )

        print("\n========== FUSION RESULTS ==========")
        for chunk in chunks:
            print(chunk)
        for chunk in chunks:
            logger.info(
                "chunk=%s | vector=%s | keyword=%s | fusion=%s",
                chunk.metadata.chunk,
                chunk.vector_score,
                chunk.keyword_score,
                chunk.fusion_score,
            )

        if not chunks:
            logger.warning("No chunks found.")
            return []

        filtered_chunks = self._filter_by_distance(chunks)

        if filtered_chunks:
            return filtered_chunks[: self.top_k]

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
            if (
                chunk.vector_score is None
                or chunk.vector_score <= self.max_distance
            )
        ]

    def _deduplicate(
        self,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Remove duplicate chunks while preserving retrieval order.
        """
        unique_chunks_map: dict[tuple[str, int, int], RetrievedChunk] = {}

        for chunk in chunks:
            key = (
                chunk.metadata.source,
                chunk.metadata.page,
                chunk.metadata.chunk,
            )

            existing = unique_chunks_map.get(key)

            if existing is None:
                unique_chunks_map[key] = chunk
            else:
                if chunk.vector_score is not None:
                    existing.vector_score = chunk.vector_score

                if chunk.keyword_score is not None:
                    existing.keyword_score = chunk.keyword_score

                if chunk.fusion_score is not None:
                    existing.fusion_score = chunk.fusion_score

        return list(unique_chunks_map.values())