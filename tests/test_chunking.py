
from unittest.mock import Mock

import pytest

from chunking import SentenceChunker, build_chunker
from models import Section


def make_section(text, heading="Introduction", page=1):
    return Section(
        heading=heading,
        level=1,
        page=page,
        text=text,
    )


def make_chunker(max_chunk_size=1000, min_chunk_size=10):
    return SentenceChunker(
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size,
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
    assert all(document.startswith("Python\n\n") for document in documents)


def test_chunk_numbers_chunks_across_sections():
    chunker = make_chunker(min_chunk_size=1)

    _, metadatas = chunker.chunk(
        [
            make_section("One. Two.", heading="A"),
            make_section("Three.", heading="B"),
        ],
        source="guide.pdf",
    )

    assert [metadata.chunk for metadata in metadatas] == [0, 1, 2]
    assert [metadata.heading for metadata in metadatas] == ["A", "A", "B"]


def test_sentences_are_packed_until_minimum_size():
    chunker = make_chunker(min_chunk_size=20)
    section = make_section("Short one. Short two. Short three. End.", heading="")

    documents, _ = chunker.chunk([section], source="guide.pdf")

    assert documents == ["Short one. Short two.", "Short three. End."]


def test_chunk_never_exceeds_maximum_size_when_sentences_fit():
    chunker = make_chunker(max_chunk_size=25, min_chunk_size=1000)
    section = make_section(
        "Alpha beta gamma. Delta epsilon. Zeta eta theta. Iota.",
        heading="",
    )

    documents, _ = chunker.chunk([section], source="guide.pdf")

    assert all(len(document) <= 25 for document in documents)
    assert " ".join(documents) == section.text


def test_build_chunker_returns_sentence_chunker_without_using_embedder():
    embedder = Mock()

    chunker = build_chunker(
        strategy="sentence",
        embedder=embedder,
        max_chunk_size=1000,
        min_chunk_size=300,
    )
    chunker.chunk([make_section("One sentence. Two sentences.")], source="a.pdf")

    assert isinstance(chunker, SentenceChunker)
    assert embedder.mock_calls == []


def test_build_chunker_rejects_unknown_strategy():
    with pytest.raises(ValueError, match="Unknown chunking strategy 'magic'"):
        build_chunker(
            strategy="magic",
            embedder=Mock(),
            max_chunk_size=1000,
            min_chunk_size=300,
        )
