from models import RetrievedChunk
from retrieval.vector_search import VectorSearch
from retrieval.keyword_search import KeywordSearch
from retrieval.fusion import ReciprocalRankFusion
from retrieval.reranker import CrossEncoderReranker

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
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
        reranker: CrossEncoderReranker,
        retrieval_top_k: int,
        final_top_k: int,
    ):
        self.vector_search = vector_search
        self.keyword_search = keyword_search
        self.fusion = fusion
        self.reranker = reranker
        self.retrieval_top_k = retrieval_top_k
        self.final_top_k = final_top_k

    def search(
        self,
        query: str,
        embedding: list[float],
    ) -> list[RetrievedChunk]:

        vector_chunks = self.vector_search.search(
            embedding=embedding,
            top_k=self.retrieval_top_k,
        )

        keyword_chunks = self.keyword_search.search(
            query=query,
            top_k=self.retrieval_top_k,
        )

        chunks = self.fusion.fuse(
            vector_chunks,
            keyword_chunks,
        )

        if not chunks:
            logger.warning("No chunks found.")
            return []


        chunks = self.reranker.rerank(
            question=query,
            chunks=chunks,
            top_k=self.final_top_k,
        )

        return chunks

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