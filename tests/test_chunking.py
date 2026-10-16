
from chunking import SemanticChunker
from models import Section


class FakeEmbedder:
    def embed_batch(self, texts):
        return [[1.0, 0.0] for _ in texts]


def make_section(text, heading="Introduction", page=1):
    return Section(
        heading=heading,
        level=1,
        page=page,
        text=text,
    )


def make_chunker():
    return SemanticChunker(
        embedder=FakeEmbedder(),
        max_chunk_size=1000,
        min_chunk_size=10,
        similarity_threshold=0.88,
    )


def test_chunk_returns_empty_results_for_empty_sections():
    chunker = make_chunker()

    documents, metadatas = chunker.chunk([], source="guide.pdf")

    assert documents == []
    assert metadatas == []


def test_chunk_ignores_sections_with_only_whitespace():
    chunker = make_chunker()

    documents, metadatas = chunker.chunk(
        [make_section("   \n   ")],
        source="guide.pdf",
    )

    assert documents == []
    assert metadatas == []


def test_chunk_preserves_source_page_and_heading():
    chunker = make_chunker()
    section = make_section(
        "Python is a programming language. It supports many applications.",
        heading="Python",
        page=3,
    )

    documents, metadatas = chunker.chunk(
        [section],
        source="guide.pdf",
    )

    assert documents
    assert len(documents) == len(metadatas)
    assert all(metadata.source == "guide.pdf" for metadata in metadatas)
    assert all(metadata.page == 3 for metadata in metadatas)
    assert all("Python" in document for document in documents)


def test_chunk_assigns_chunk_metadata():
    chunker = make_chunker()
    section = make_section(
        "First sentence describes Python. Second sentence describes its uses.",
    )

    documents, metadatas = chunker.chunk(
        [section],
        source="guide.pdf",
    )

    assert len(documents) == len(metadatas)
    assert all(metadata.chunk >= 0 for metadata in metadatas)
