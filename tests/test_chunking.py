
from unittest.mock import Mock

import pytest

from chunking import (
    SemanticChunker,
    SentenceChunker,
    build_chunker,
    chunking_id,
    document_title,
    strip_context,
)
from models import Section


class TopicEmbedder:
    """Embeds text as counts of the words 'cat' and 'dog', so the distance
    between windows grows where the text moves from cats to dogs."""

    def __init__(self):
        self.calls = []

    def embed_batch(self, texts):
        self.calls.append(texts)
        return [
            [text.lower().count("cat"), text.lower().count("dog")]
            for text in texts
        ]


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


def test_chunks_are_built_from_cleaned_text():
    chunker = make_chunker(min_chunk_size=1000)
    section = make_section("First  sentence\twith   gaps.\r\nSecond one.", heading="")

    documents, _ = chunker.chunk([section], source="guide.pdf")

    assert documents == ["First sentence with gaps. Second one."]


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


def make_semantic_chunker(
    embedder=None,
    max_chunk_size=1000,
    min_chunk_size=1,
    breakpoint_percentile=80,
    window=1,
):
    return SemanticChunker(
        embedder=embedder or TopicEmbedder(),
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size,
        breakpoint_percentile=breakpoint_percentile,
        window=window,
    )


CATS_THEN_DOGS = "Cats purr. Cats nap. Cats hunt. Dogs bark. Dogs fetch. Dogs guard."


def test_semantic_chunker_splits_where_the_topic_changes():
    chunker = make_semantic_chunker()

    documents, _ = chunker.chunk(
        [make_section(CATS_THEN_DOGS, heading="")],
        source="pets.pdf",
    )

    assert documents == [
        "Cats purr. Cats nap. Cats hunt.",
        "Dogs bark. Dogs fetch. Dogs guard.",
    ]


def test_semantic_chunker_embeds_windows_of_neighbouring_sentences():
    embedder = TopicEmbedder()
    chunker = make_semantic_chunker(embedder=embedder)

    chunker.chunk([make_section("One cat. Two cats. Three cats.")], source="a.pdf")

    assert embedder.calls == [[
        "One cat. Two cats.",
        "One cat. Two cats. Three cats.",
        "Two cats. Three cats.",
    ]]


def test_semantic_breakpoints_use_a_document_wide_threshold():
    # Within its own section the mild shift in the second section would be
    # a breakpoint; against the whole document it is not.
    chunker = make_semantic_chunker()

    documents, _ = chunker.chunk(
        [
            make_section(CATS_THEN_DOGS, heading="A"),
            make_section(
                "Cats purr. Cats nap. Cats and a dog. Cats hunt.",
                heading="B",
            ),
        ],
        source="pets.pdf",
    )

    assert [document for document in documents if document.startswith("B")] == [
        "B\n\nCats purr. Cats nap. Cats and a dog. Cats hunt.",
    ]


def test_semantic_chunker_merges_segments_below_minimum_size():
    chunker = make_semantic_chunker(min_chunk_size=1000)

    documents, _ = chunker.chunk(
        [make_section(CATS_THEN_DOGS, heading="")],
        source="pets.pdf",
    )

    assert documents == [CATS_THEN_DOGS]


def test_short_last_segment_joins_the_previous_one():
    chunker = make_semantic_chunker(min_chunk_size=10)

    merged = chunker._merge_small_segments([["a" * 30], ["b" * 5]])

    assert merged == [["a" * 30, "b" * 5]]


def test_short_last_segment_joins_its_own_neighbour():
    chunker = make_semantic_chunker(min_chunk_size=10)

    merged = chunker._merge_small_segments([["x" * 30], ["y" * 30], ["z" * 5]])

    assert merged == [["x" * 30], ["y" * 30, "z" * 5]]


def test_semantic_chunker_splits_large_segments_into_balanced_parts():
    chunker = make_semantic_chunker(max_chunk_size=40)
    text = "Cats purr. Cats nap. Cats hunt. Cats sleep. Cats eat. Cats play."

    documents, _ = chunker.chunk([make_section(text, heading="")], source="a.pdf")

    assert all(len(document) <= 40 for document in documents)
    assert " ".join(documents) == text
    assert len(documents) == 2


def test_semantic_chunker_handles_single_sentence_sections():
    embedder = TopicEmbedder()
    chunker = make_semantic_chunker(embedder=embedder)

    documents, _ = chunker.chunk([make_section("Only one.", heading="")], source="a.pdf")

    assert documents == ["Only one."]
    assert embedder.calls == []


def test_semantic_chunker_rejects_invalid_percentile():
    with pytest.raises(ValueError, match="breakpoint_percentile"):
        make_semantic_chunker(breakpoint_percentile=100)


def test_build_chunker_returns_semantic_chunker():
    chunker = build_chunker(
        strategy="semantic",
        embedder=TopicEmbedder(),
        max_chunk_size=1000,
        min_chunk_size=300,
        breakpoint_percentile=95,
        window=2,
    )

    assert isinstance(chunker, SemanticChunker)
    assert chunker.breakpoint_percentile == 95
    assert chunker.window == 2


def test_chunking_id_includes_semantic_parameters():
    assert chunking_id("sentence", 90, 1) == "sentence"
    assert chunking_id("semantic", 90, 1) == "semantic-p90-w1"


def test_document_title_is_the_first_heading():
    sections = [
        make_section("Intro.", heading="", page=1),
        make_section("Body.", heading="Guide to Python", page=2),
        make_section("More.", heading="Setup", page=3),
    ]

    assert document_title(sections, "guide.pdf") == "Guide to Python"


def test_document_title_falls_back_to_the_file_name():
    assert document_title([make_section("Text.", heading="")], "notes.txt") == "notes"


def test_chunks_record_the_document_title_in_metadata():
    chunker = make_chunker()

    documents, metadatas = chunker.chunk(
        [make_section("Python is popular.", heading="Python Guide")],
        source="guide.pdf",
    )

    assert metadatas[0].title == "Python Guide"
    # Without include_title the chunk text is unchanged.
    assert documents == ["Python Guide\n\nPython is popular."]


def test_include_title_prefixes_chunks_with_the_document_title():
    chunker = make_chunker()
    chunker.include_title = True

    documents, _ = chunker.chunk(
        [
            make_section("Overview text.", heading="Python Guide"),
            make_section("Install it.", heading="Setup"),
        ],
        source="guide.pdf",
    )

    assert documents == [
        # The first section is named like the document, so it is not repeated.
        "Python Guide\n\nOverview text.",
        "Python Guide\nSetup\n\nInstall it.",
    ]


def test_include_title_without_headings_uses_the_file_name():
    chunker = make_chunker()
    chunker.include_title = True

    documents, _ = chunker.chunk([make_section("Plain text.", heading="")], source="notes.txt")

    assert documents == ["notes\n\nPlain text."]


@pytest.mark.parametrize(
    "document, expected",
    [
        ("Guide\nSetup\n\nInstall it.", "Install it."),
        ("Guide\n\nInstall it.", "Install it."),
        ("Setup\n\nInstall it.", "Install it."),
        ("Install it.\n\nThen run it.", "Install it.\n\nThen run it."),
    ],
)
def test_strip_context_removes_only_the_added_lines(document, expected):
    assert strip_context(document, "Guide", "Setup") == expected


def test_chunking_id_marks_title_context():
    assert chunking_id("sentence", 90, 1, include_title=True) == "sentence-ctx"
    assert chunking_id("semantic", 90, 1, include_title=True) == "semantic-p90-w1-ctx"


def test_build_chunker_passes_include_title():
    sentence = build_chunker("sentence", None, 1000, 300, include_title=True)
    semantic = build_chunker("semantic", TopicEmbedder(), 1000, 300, include_title=True)

    assert sentence.include_title is True
    assert semantic.include_title is True
