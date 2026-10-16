import re

from rank_bm25 import BM25Okapi

from models import ChunkMetadata, RetrievedChunk
from vector_store import VectorStore

# Words, optionally joined by hyphens, so "cross-cutting?" -> "cross-cutting".
TOKEN_PATTERN = re.compile(r"\w+(?:-\w+)*")

# Common English function words. They carry no topical signal but appear in
# almost every question ("which", "is", "as"), so they skew BM25 scores toward
# chunks that merely repeat them.
STOPWORDS = frozenset(
    """
    a an and are as at be been being but by can could did do does for from
    had has have how if in into is it its may might of on or should so than
    that the their then there these they this those to was were what when
    where which while who whom why will with would
    """.split()
)


class KeywordSearch:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

        self._bm25: BM25Okapi | None = None
        self._documents: list[str] = []
        self._metadatas: list[ChunkMetadata] = []

    def rebuild(self) -> None:
        documents, metadatas = self.vector_store.get_all_chunks()

        self._documents = documents
        self._metadatas = metadatas

        if not documents:
            self._bm25 = None
            return

        tokenized_documents = [
            self._tokenize(document)
            for document in documents
        ]

        self._bm25 = BM25Okapi(tokenized_documents)

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
        return [
            token
            for token in TOKEN_PATTERN.findall(text.lower())
            if token not in STOPWORDS
        ]
