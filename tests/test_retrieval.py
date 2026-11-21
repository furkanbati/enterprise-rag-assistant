
from unittest.mock import Mock

import pytest

import retrieval.reranker as reranker_module
from models import ChunkMetadata, RetrievedChunk
from retrieval.fusion import ReciprocalRankFusion
from retrieval.reranker import CrossEncoderReranker
from retrieval.retriever import Retriever
from retrieval.vector_search import VectorSearch


def make_chunk(
    source="guide.pdf",
    page=1,
    chunk=0,
    document="Python is a programming language.",
    vector_score=None,
    keyword_score=None,
):
    return RetrievedChunk(
        document=document,
        metadata=ChunkMetadata(
            source=source,
            page=page,
            chunk=chunk,
            heading="Introduction",
            level=1,
        ),
        vector_score=vector_score,
        keyword_score=keyword_score,
    )


def test_vector_search_forwards_embedding_and_top_k():
    vector_store = Mock()
    expected = [make_chunk()]
    vector_store.query.return_value = expected

    search = VectorSearch(vector_store)

    results = search.search(
        embedding=[0.1, 0.2],
        top_k=5,
    )

    assert results == expected
    vector_store.query.assert_called_once_with(
        embedding=[0.1, 0.2],
        top_k=5,
    )


def test_fusion_combines_duplicate_chunks_from_both_searches():
    vector_chunk = make_chunk(vector_score=0.2)
    keyword_chunk = make_chunk(keyword_score=4.5)

    fusion = ReciprocalRankFusion(k=60)

    results = fusion.fuse(
        [vector_chunk],
        [keyword_chunk],
    )

    assert len(results) == 1
    assert results[0].metadata == vector_chunk.metadata
    assert results[0].fusion_score == (1 / 61) + (1 / 61)
    assert results[0].vector_score == 0.2
    assert results[0].keyword_score == 4.5


def test_fusion_orders_chunks_by_combined_score():
    first = make_chunk(
        source="first.pdf",
        chunk=0,
        document="First document",
    )
    second = make_chunk(
        source="second.pdf",
        chunk=0,
        document="Second document",
    )

    fusion = ReciprocalRankFusion(k=60)

    results = fusion.fuse(
        [first, second],
        [second, first],
    )

    assert len(results) == 2
    assert results[0].fusion_score == results[1].fusion_score


def test_fusion_does_not_mutate_original_chunks():
    original = make_chunk(vector_score=0.3)

    ReciprocalRankFusion().fuse([original], [])

    assert original.fusion_score is None


def test_reranker_returns_empty_for_empty_chunks():
    reranker = CrossEncoderReranker("test-model")

    assert reranker.rerank("question", [], top_k=3) == []
    assert reranker.model is None


def test_reranker_loads_model_lazily_and_sorts_by_score(monkeypatch):
    class FakeCrossEncoder:
        def __init__(self, model_name):
            self.model_name = model_name
            self.received_pairs = None
            self.batch_size = None

        def predict(self, pairs, batch_size):
            self.received_pairs = pairs
            self.batch_size = batch_size
            return [0.2, 0.9]

    monkeypatch.setattr(
        reranker_module,
        "CrossEncoder",
        FakeCrossEncoder,
    )

    lower = make_chunk(document="Lower relevance")
    higher = make_chunk(
        source="other.pdf",
        document="Higher relevance",
    )
    chunks = [lower, higher]

    reranker = CrossEncoderReranker("test-model")

    assert reranker.model is None

    results = reranker.rerank(
        "test question",
        chunks,
        top_k=1,
    )

    assert reranker.model.model_name == "test-model"
    assert reranker.model.received_pairs == [
        ("test question", "Lower relevance"),
        ("test question", "Higher relevance"),
    ]
    assert reranker.model.batch_size == 16
    assert results == [higher]
    assert higher.rerank_score == 0.9
    assert lower.rerank_score == 0.2


def test_retriever_runs_search_fusion_and_reranking():
    vector_chunk = make_chunk(vector_score=0.2)
    keyword_chunk = make_chunk(keyword_score=3.0)
    fused_chunk = make_chunk()
    final_chunk = make_chunk()

    vector_search = Mock()
    vector_search.search.return_value = [vector_chunk]

    keyword_search = Mock()
    keyword_search.search.return_value = [keyword_chunk]

    fusion = Mock()
    fusion.fuse.return_value = [fused_chunk]

    reranker = Mock()
    reranker.rerank.return_value = [final_chunk]

    retriever = Retriever(
        vector_search=vector_search,
        keyword_search=keyword_search,
        fusion=fusion,
        reranker=reranker,
        retrieval_top_k=10,
        final_top_k=3,
    )

    results = retriever.search(
        query="Python",
        embedding=[0.1, 0.2],
    )

    assert results == [final_chunk]

    vector_search.search.assert_called_once_with(
        embedding=[0.1, 0.2],
        top_k=10,
    )
    keyword_search.search.assert_called_once_with(
        query="Python",
        top_k=10,
    )
    fusion.fuse.assert_called_once_with(
        [vector_chunk],
        [keyword_chunk],
    )
    reranker.rerank.assert_called_once_with(
        question="Python",
        chunks=[fused_chunk],
        top_k=3,
    )


def test_retriever_returns_empty_when_fusion_finds_no_chunks():
    vector_search = Mock()
    vector_search.search.return_value = []

    keyword_search = Mock()
    keyword_search.search.return_value = []

    fusion = Mock()
    fusion.fuse.return_value = []

    reranker = Mock()

    retriever = Retriever(
        vector_search=vector_search,
        keyword_search=keyword_search,
        fusion=fusion,
        reranker=reranker,
        retrieval_top_k=10,
        final_top_k=3,
    )

    results = retriever.search(
        query="Unknown topic",
        embedding=[0.1, 0.2],
    )

    assert results == []
    reranker.rerank.assert_not_called()


def test_reranker_load_loads_the_model_once(monkeypatch):
    loaded = []

    class FakeCrossEncoder:
        def __init__(self, model_name):
            loaded.append(model_name)

    monkeypatch.setattr(reranker_module, "CrossEncoder", FakeCrossEncoder)

    reranker = CrossEncoderReranker("test-model")
    reranker.load()
    reranker.load()

    assert loaded == ["test-model"]
    assert isinstance(reranker.model, FakeCrossEncoder)


def make_routed_retriever():
    default, turkish = Mock(), Mock()
    default.rerank.return_value = ["default"]
    turkish.rerank.return_value = ["turkish"]
    fusion = Mock()
    fusion.fuse.return_value = [make_chunk()]

    retriever = Retriever(
        vector_search=Mock(),
        keyword_search=Mock(),
        fusion=fusion,
        reranker=default,
        retrieval_top_k=10,
        final_top_k=3,
        language_rerankers={"tr": turkish},
    )

    return retriever, default, turkish


def test_retriever_reranks_turkish_questions_with_the_turkish_reranker():
    retriever, default, turkish = make_routed_retriever()

    assert retriever.search(query="Q", embedding=[0.1], language="tr") == ["turkish"]
    default.rerank.assert_not_called()


@pytest.mark.parametrize("language", ["en", "de"])
def test_retriever_uses_the_default_reranker_for_other_languages(language):
    retriever, default, turkish = make_routed_retriever()

    assert retriever.search(query="Q", embedding=[0.1], language=language) == ["default"]
    turkish.rerank.assert_not_called()
