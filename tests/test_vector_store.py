
from dataclasses import asdict

import pytest

from models import ChunkMetadata
from vector_store import VectorStore, collection_name_for


class FakeCollection:
    def __init__(self, metadata=None):
        self.metadata = metadata
        self.added = None
        self.query_result = {
            "documents": [["Python machine learning"]],
            "metadatas": [[
                {
                    "source": "guide.pdf",
                    "page": 1,
                    "chunk": 0,
                    "heading": "Introduction",
                    "level": 1,
                }
            ]],
            "distances": [[0.15]],
        }
        self.get_result = {
            "documents": ["Python machine learning"],
            "metadatas": [{
                "source": "guide.pdf",
                "page": 1,
                "chunk": 0,
                "heading": "Introduction",
                "level": 1,
            }],
        }

    def add(self, **kwargs):
        self.added = kwargs

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return self.query_result

    def get(self, **kwargs):
        self.get_kwargs = kwargs
        return self.get_result


class FakeClient:
    def __init__(self, collection):
        self.collection = collection
        self.path = None

    def get_or_create_collection(self, name, metadata=None):
        self.collection_name = name

        # Like Chroma: metadata is only set when the collection is created.
        if self.collection.metadata is None:
            self.collection.metadata = metadata

        return self.collection


def make_metadata() -> ChunkMetadata:
    return ChunkMetadata(
        source="guide.pdf",
        page=1,
        chunk=0,
        heading="Introduction",
        level=1,
    )


def make_store(monkeypatch, embedding_model=None, stored_metadata=None):
    import vector_store

    collection = FakeCollection(metadata=stored_metadata)
    client = FakeClient(collection)

    def fake_persistent_client(path):
        client.path = path
        return client

    monkeypatch.setattr(
        vector_store.chromadb,
        "PersistentClient",
        fake_persistent_client,
    )

    store = VectorStore(
        path="./test-data",
        collection_name="test-documents",
        embedding_model=embedding_model,
    )
    return store, collection, client


def test_initializes_persistent_client_and_collection(monkeypatch):
    store, collection, client = make_store(monkeypatch)

    assert store.collection is collection
    assert client.path == "./test-data"
    assert client.collection_name == "test-documents"


def test_add_passes_documents_embeddings_and_metadata(monkeypatch):
    store, collection, _ = make_store(monkeypatch)
    metadata = make_metadata()

    store.add(
        documents=["Python machine learning"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[metadata],
    )

    assert collection.added["documents"] == ["Python machine learning"]
    assert collection.added["embeddings"] == [[0.1, 0.2, 0.3]]
    assert collection.added["metadatas"] == [asdict(metadata)]
    assert len(collection.added["ids"]) == 1


def test_query_returns_retrieved_chunks_with_metadata(monkeypatch):
    store, collection, _ = make_store(monkeypatch)

    results = store.query(embedding=[0.1, 0.2], top_k=1)

    assert len(results) == 1
    assert results[0].document == "Python machine learning"
    assert results[0].metadata == make_metadata()
    assert results[0].vector_score == 0.15
    assert collection.query_kwargs["n_results"] == 1
    assert collection.query_kwargs["query_embeddings"] == [[0.1, 0.2]]


def test_get_all_chunks_returns_documents_and_metadata(monkeypatch):
    store, _, _ = make_store(monkeypatch)

    documents, metadatas = store.get_all_chunks()

    assert documents == ["Python machine learning"]
    assert metadatas == [make_metadata()]


def test_get_all_chunks_handles_empty_results(monkeypatch):
    store, collection, _ = make_store(monkeypatch)
    collection.get_result = {
        "documents": None,
        "metadatas": None,
    }

    documents, metadatas = store.get_all_chunks()

    assert documents == []
    assert metadatas == []


def test_collection_name_includes_provider_model_and_chunking():
    assert (
        collection_name_for("documents", "ollama", "nomic-embed-text", "sentence")
        == "documents__ollama__nomic-embed-text__sentence"
    )


def test_collection_name_replaces_characters_chroma_rejects():
    assert (
        collection_name_for(
            "documents", "ollama", "nomic-embed-text:latest", "sentence"
        )
        == "documents__ollama__nomic-embed-text-latest__sentence"
    )


def test_new_collection_records_embedding_model(monkeypatch):
    _, collection, _ = make_store(
        monkeypatch,
        embedding_model="openai/text-embedding-3-small",
    )

    assert collection.metadata == {
        "embedding_model": "openai/text-embedding-3-small"
    }


def test_existing_collection_with_same_model_opens(monkeypatch):
    store, collection, _ = make_store(
        monkeypatch,
        embedding_model="ollama/nomic-embed-text",
        stored_metadata={"embedding_model": "ollama/nomic-embed-text"},
    )

    assert store.collection is collection


def test_existing_collection_with_other_model_is_rejected(monkeypatch):
    with pytest.raises(
        ValueError,
        match="holds embeddings from 'ollama/nomic-embed-text'",
    ):
        make_store(
            monkeypatch,
            embedding_model="openai/text-embedding-3-small",
            stored_metadata={"embedding_model": "ollama/nomic-embed-text"},
        )
