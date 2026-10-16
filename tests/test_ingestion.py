
from pathlib import Path

import ingestion as ingestion_module
from ingestion import Ingestion
from models import ChunkMetadata, Section


class FakeParser:
    def parse(self, pdf_path):
        self.pdf_path = pdf_path
        return [
            Section(
                heading="Python",
                level=1,
                page=1,
                text="Python is a programming language.",
            )
        ]


class FakeChunker:
    def __init__(self):
        self.sections = None
        self.source = None

    def chunk(self, sections, source):
        self.sections = sections
        self.source = source
        return (
            ["Python is a programming language."],
            [
                ChunkMetadata(
                    source=source,
                    page=1,
                    chunk=0,
                    heading="Python",
                    level=1,
                )
            ],
        )


class FakeEmbedder:
    def __init__(self):
        self.documents = None

    def embed_batch(self, documents):
        self.documents = documents
        return [[0.1, 0.2, 0.3] for _ in documents]


class FakeVectorStore:
    def __init__(self):
        self.added = None

    def add(self, documents, embeddings, metadatas):
        self.added = (documents, embeddings, metadatas)


class FakeKeywordSearch:
    def __init__(self):
        self.rebuild_called = False

    def rebuild(self):
        self.rebuild_called = True


def make_ingestion(monkeypatch, chunker):
    parser = FakeParser()
    monkeypatch.setattr(
        ingestion_module,
        "DocumentParser",
        lambda: parser,
    )

    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    keyword_search = FakeKeywordSearch()

    service = Ingestion(
        embedder=embedder,
        vector_store=vector_store,
        chunker=chunker,
        keyword_search=keyword_search,
    )

    return (
        service,
        parser,
        embedder,
        vector_store,
        keyword_search,
    )


def test_ingest_parses_embeds_stores_and_rebuilds_index(monkeypatch):
    chunker = FakeChunker()
    (
        service,
        parser,
        embedder,
        vector_store,
        keyword_search,
    ) = make_ingestion(monkeypatch, chunker)

    service.ingest("/tmp/guide.pdf")

    assert parser.pdf_path == "/tmp/guide.pdf"
    assert chunker.source == Path("/tmp/guide.pdf").name
    assert chunker.sections
    assert embedder.documents == [
        "Python is a programming language."
    ]

    documents, embeddings, metadatas = vector_store.added

    assert documents == embedder.documents
    assert embeddings == [[0.1, 0.2, 0.3]]
    assert metadatas[0].source == "guide.pdf"
    assert metadatas[0].page == 1
    assert keyword_search.rebuild_called


def test_ingest_handles_empty_chunk_results(monkeypatch):
    class EmptyChunker:
        def chunk(self, sections, source):
            return [], []

    (
        service,
        _,
        embedder,
        vector_store,
        keyword_search,
    ) = make_ingestion(monkeypatch, EmptyChunker())

    service.ingest("/tmp/empty.pdf")

    assert embedder.documents == []
    assert vector_store.added == ([], [], [])
    assert keyword_search.rebuild_called
 