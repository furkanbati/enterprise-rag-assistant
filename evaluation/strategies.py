from typing import Protocol

from language import detect_language
from models import RetrievedChunk
from retrieval.fusion import ReciprocalRankFusion
from retrieval.keyword_search import KeywordSearch
from retrieval.reranker import CrossEncoderReranker
from retrieval.vector_search import VectorSearch


class RetrievalStrategy(Protocol):
    """A retrieval configuration that can be compared during evaluation."""

    def retrieve(
        self,
        question: str,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        ...


class VectorOnlyStrategy:
    def __init__(self, vector_search: VectorSearch) -> None:
        self.vector_search = vector_search

    def retrieve(
        self,
        question: str,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        return self.vector_search.search(
            embedding=embedding,
            top_k=top_k,
        )


class KeywordOnlyStrategy:
    def __init__(self, keyword_search: KeywordSearch) -> None:
        self.keyword_search = keyword_search

    def retrieve(
        self,
        question: str,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        return self.keyword_search.search(
            query=question,
            top_k=top_k,
        )


class HybridStrategy:
    """Vector search and BM25 combined with Reciprocal Rank Fusion."""

    def __init__(
        self,
        vector_search: VectorSearch,
        keyword_search: KeywordSearch,
        fusion: ReciprocalRankFusion,
        candidate_top_k: int,
    ) -> None:
        self.vector_search = vector_search
        self.keyword_search = keyword_search
        self.fusion = fusion
        self.candidate_top_k = candidate_top_k

    def retrieve(
        self,
        question: str,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        return self._fused_candidates(question, embedding)[:top_k]

    def _fused_candidates(
        self,
        question: str,
        embedding: list[float],
    ) -> list[RetrievedChunk]:
        candidate_top_k = max(self.candidate_top_k, 1)

        vector_chunks = self.vector_search.search(
            embedding=embedding,
            top_k=candidate_top_k,
        )

        keyword_chunks = self.keyword_search.search(
            query=question,
            top_k=candidate_top_k,
        )

        return self.fusion.fuse(vector_chunks, keyword_chunks)


class HybridRerankStrategy(HybridStrategy):
    """Hybrid retrieval followed by cross-encoder reranking (production setup).

    Like the API, a question in a language listed in ``language_rerankers``
    is reranked by that language's reranker."""

    def __init__(
        self,
        vector_search: VectorSearch,
        keyword_search: KeywordSearch,
        fusion: ReciprocalRankFusion,
        reranker: CrossEncoderReranker,
        candidate_top_k: int,
        language_rerankers: dict[str, CrossEncoderReranker] | None = None,
    ) -> None:
        super().__init__(
            vector_search=vector_search,
            keyword_search=keyword_search,
            fusion=fusion,
            candidate_top_k=candidate_top_k,
        )
        self.reranker = reranker
        self.language_rerankers = language_rerankers or {}

    def rerankers(self) -> list[CrossEncoderReranker]:
        return [self.reranker, *self.language_rerankers.values()]

    def retrieve(
        self,
        question: str,
        embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        candidates = self._fused_candidates(question, embedding)
        reranker = self.language_rerankers.get(
            detect_language(question),
            self.reranker,
        )

        return reranker.rerank(
            question=question,
            chunks=candidates,
            top_k=top_k,
        )
