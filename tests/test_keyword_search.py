
from retrieval.keyword_search import KeywordSearch
from models import ChunkMetadata


class FakeVectorStore:
    def __init__(self, documents=None, metadatas=None):
        self.documents = documents if documents is not None else []
        self.metadatas = metadatas if metadatas is not None else []

    def get_all_chunks(self):
        return self.documents, self.metadatas


def make_metadata(chunk_id: int) -> ChunkMetadata:
    return ChunkMetadata(
        source="guide.pdf",
        page=1,
        chunk=chunk_id,
        heading="Introduction",
        level=1,
    )


def test_rebuild_with_empty_store_does_not_raise():
    search = KeywordSearch(FakeVectorStore())

    search.rebuild()

    assert search._bm25 is None


def test_search_with_empty_store_returns_empty_list():
    search = KeywordSearch(FakeVectorStore())

    search.rebuild()

    assert search.search("artificial intelligence", top_k=3) == []


def test_rebuild_indexes_documents():
    documents = ["python machine learning", "fresh cooking ingredients"]
    metadatas = [make_metadata(0), make_metadata(1)]
    search = KeywordSearch(FakeVectorStore(documents, metadatas))

    search.rebuild()

    assert search._bm25 is not None
    assert search._documents == documents
    assert search._metadatas == metadatas


def test_search_returns_relevant_document_and_metadata():
    documents = [
        "python machine learning",
        "fresh cooking ingredients",
    ]
    metadatas = [make_metadata(0), make_metadata(1)]
    search = KeywordSearch(FakeVectorStore(documents, metadatas))
    search.rebuild()

    results = search.search("python machine learning", top_k=1)

    assert len(results) == 1
    assert results[0].document == documents[0]
    assert results[0].metadata == metadatas[0]
    assert results[0].keyword_score is not None


def test_rebuild_empty_store_clears_previous_index():
    store = FakeVectorStore(
        ["python machine learning"],
        [make_metadata(0)],
    )
    search = KeywordSearch(store)
    search.rebuild()

    store.documents = []
    store.metadatas = []
    search.rebuild()

    assert search._bm25 is None
    assert search.search("python", top_k=3) == []


def test_search_respects_top_k():
    documents = [
        "python machine learning",
        "python programming language",
        "fresh cooking ingredients",
    ]
    metadatas = [make_metadata(i) for i in range(len(documents))]
    search = KeywordSearch(FakeVectorStore(documents, metadatas))
    search.rebuild()

    results = search.search("python", top_k=1)

    assert len(results) == 1
    assert results[0].document in documents[:2]


def test_tokenize_strips_punctuation_and_stopwords():
    search = KeywordSearch(FakeVectorStore())

    assert search._tokenize(
        "Which AI RMF function is described as cross-cutting?"
    ) == ["ai", "rmf", "function", "described", "cross-cutting"]


def test_search_matches_terms_followed_by_punctuation():
    documents = [
        "GOVERN is a cross-cutting function.",
        "Which function is described here? It is the MAP function.",
        "fresh cooking ingredients",
    ]
    metadatas = [make_metadata(i) for i in range(len(documents))]
    search = KeywordSearch(FakeVectorStore(documents, metadatas))
    search.rebuild()

    results = search.search("Which function is cross-cutting?", top_k=1)

    assert results[0].document == documents[0]
