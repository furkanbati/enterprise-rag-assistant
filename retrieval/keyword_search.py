from rank_bm25 import BM25Okapi

from models import ChunkMetadata, RetrievedChunk
from vector_store import VectorStore


class KeywordSearch:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

        self._bm25: BM25Okapi | None = None
        self._documents: list[str] = []
        self._metadatas: list[ChunkMetadata] = []

    def rebuild(self) -> None:
        documents, metadatas = self.vector_store.get_all_chunks()

        tokenized_documents = [
            self._tokenize(document)
            for document in documents
        ]

        self._bm25 = BM25Okapi(tokenized_documents)
        self._documents = documents
        self._metadatas = metadatas

    def search(
        self,
        query: str,
        top_k: int,
    ) -> list[RetrievedChunk]:
        if self._bm25 is None:
            return []

        tokenized_query = self._tokenize(query)

        scores = self._bm25.get_scores(tokenized_query)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        return [
            RetrievedChunk(
                document=self._documents[index],
                metadata=self._metadatas[index],
                keyword_score=float(score),
            )
            for index, score in ranked
        ]

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()