import math
import re
from pathlib import Path
from typing import Protocol

from providers.base import Embedder
from models import ChunkMetadata, Section

CHUNKING_STRATEGIES = ("sentence", "semantic")


class Chunker(Protocol):
    """Splits parsed document sections into chunks with metadata."""

    def chunk(
        self,
        sections: list[Section],
        source: str,
    ) -> tuple[list[str], list[ChunkMetadata]]: ...


class SentenceChunker:
    """Packs the whole sentences of each section into chunks of roughly
    min_chunk_size to max_chunk_size characters.

    Chunks never cross a section boundary, and each chunk is prefixed with
    its section heading. With include_title, the document title is prefixed
    as well, so that search can tell apart documents with similar content.
    """

    def __init__(
        self,
        max_chunk_size: int,
        min_chunk_size: int,
        include_title: bool = False,
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.include_title = include_title

    def chunk(
        self,
        sections: list[Section],
        source: str,
    ) -> tuple[list[str], list[ChunkMetadata]]:
        """
        Main entry point for document chunking.
        """

        prepared: list[tuple[Section, list[str]]] = []

        for section in sections:
            text = self._clean_text(section.text)

            if text:
                prepared.append((section, self._split_sentences(text)))

        section_chunks = self._split_document(
            [sentences for _, sentences in prepared]
        )

        title = document_title(sections, source)

        documents: list[str] = []
        metadatas: list[ChunkMetadata] = []

        chunk_id = 0

        for (section, _), chunks in zip(prepared, section_chunks):
            for chunk in chunks:
                documents.append(
                    self._with_context(chunk, title, section.heading)
                )

                metadatas.append(
                    ChunkMetadata(
                        source=source,
                        page=section.page,
                        chunk=chunk_id,
                        heading=section.heading,
                        level=section.level,
                        title=title,
                    )
                )

                chunk_id += 1

        return documents, metadatas

    def _with_context(self, chunk: str, title: str, heading: str) -> str:
        """Prefix a chunk with the title (if enabled) and section heading."""

        lines = [title] if self.include_title else []

        # A section named like the document would only repeat the title.
        if heading and heading not in lines:
            lines.append(heading)

        if not lines:
            return chunk

        return "\n".join(lines) + "\n\n" + chunk

    def _split_document(
        self,
        sections: list[list[str]],
    ) -> list[list[str]]:
        """Split the sentences of every section of one document into chunks."""

        return [self._split(sentences) for sentences in sections]

    def _split(self, sentences: list[str]) -> list[str]:
        """
        Pack consecutive sentences into chunks.

        A new chunk is started when:
        - the current chunk has reached the minimum chunk size
        - the maximum chunk size would be exceeded
        """

        if not sentences:
            return []

        chunks: list[str] = []

        current_chunk = [sentences[0]]
        current_length = len(sentences[0])

        for sentence in sentences[1:]:
            should_split = (
                current_length >= self.min_chunk_size
                or current_length + len(sentence) > self.max_chunk_size
            )

            if should_split:
                chunks.append(" ".join(current_chunk))

                current_chunk = [sentence]
                current_length = len(sentence)

            else:
                current_chunk.append(sentence)
                current_length += len(sentence)

        chunks.append(" ".join(current_chunk))

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Normalize extracted PDF text.
        """

        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _split_sentences(
        self,
        text: str,
    ) -> list[str]:
        """
        Very lightweight sentence splitter.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [s.strip() for s in sentences if s.strip()]


class SemanticChunker(SentenceChunker):
    """Splits sections where the topic shifts.

    Each sentence is embedded together with its neighbours (``window``
    sentences on each side), and the distance between consecutive windows
    measures how much the topic changes at each sentence boundary. A
    boundary becomes a breakpoint when its distance is above the given
    percentile of all boundary distances in the document, so the threshold
    adapts to the document and the embedding model instead of being a fixed
    similarity value.

    Segments shorter than min_chunk_size are merged with the next segment,
    and segments longer than max_chunk_size are split into balanced parts at
    sentence boundaries.
    """

    def __init__(
        self,
        embedder: Embedder,
        max_chunk_size: int,
        min_chunk_size: int,
        breakpoint_percentile: int,
        window: int,
        include_title: bool = False,
    ) -> None:
        super().__init__(
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
            include_title=include_title,
        )

        if not 0 < breakpoint_percentile < 100:
            raise ValueError("breakpoint_percentile must be between 0 and 100.")

        if window < 0:
            raise ValueError("window must not be negative.")

        self.embedder = embedder
        self.breakpoint_percentile = breakpoint_percentile
        self.window = window

    def _split_document(
        self,
        sections: list[list[str]],
    ) -> list[list[str]]:
        distances = [self._distances(sentences) for sentences in sections]
        all_distances = [
            distance
            for section_distances in distances
            for distance in section_distances
        ]

        threshold = (
            _percentile(all_distances, self.breakpoint_percentile)
            if all_distances
            else math.inf
        )

        return [
            self._split_at_breakpoints(sentences, section_distances, threshold)
            for sentences, section_distances in zip(sections, distances)
        ]

    def _distances(self, sentences: list[str]) -> list[float]:
        """Distance between the windows around each pair of consecutive
        sentences."""

        if len(sentences) < 2:
            return []

        windows = [
            " ".join(sentences[max(0, i - self.window):i + self.window + 1])
            for i in range(len(sentences))
        ]
        embeddings = self.embedder.embed_batch(windows)

        return [
            1 - _cosine_similarity(current, following)
            for current, following in zip(embeddings, embeddings[1:])
        ]

    def _split_at_breakpoints(
        self,
        sentences: list[str],
        distances: list[float],
        threshold: float,
    ) -> list[str]:
        if not sentences:
            return []

        segments = [[sentences[0]]]

        for sentence, distance in zip(sentences[1:], distances):
            if distance > threshold:
                segments.append([sentence])
            else:
                segments[-1].append(sentence)

        chunks: list[str] = []

        for segment in self._merge_small_segments(segments):
            chunks.extend(self._split_large_segment(segment))

        return chunks

    def _merge_small_segments(
        self,
        segments: list[list[str]],
    ) -> list[list[str]]:
        merged: list[list[str]] = []

        for segment in segments:
            if (
                merged
                and _length(merged[-1]) < self.min_chunk_size
                and _length(merged[-1] + segment) <= self.max_chunk_size
            ):
                merged[-1] = merged[-1] + segment
            else:
                merged.append(segment)

        # A short last segment has no next segment, so it joins the previous one.
        if (
            len(merged) > 1
            and _length(merged[-1]) < self.min_chunk_size
            and _length(merged[-2] + merged[-1]) <= self.max_chunk_size
        ):
            last = merged.pop()
            merged[-1] = merged[-1] + last

        return merged

    def _split_large_segment(self, segment: list[str]) -> list[str]:
        """Split a segment into parts of similar length, each at most
        max_chunk_size characters unless a single sentence is longer."""

        total = _length(segment)
        parts = math.ceil(total / self.max_chunk_size)
        target = total / parts

        chunks: list[str] = []
        current: list[str] = []

        for sentence in segment:
            if current and (
                _length(current + [sentence]) > self.max_chunk_size
                or _length(current) >= target
            ):
                chunks.append(" ".join(current))
                current = []

            current.append(sentence)

        chunks.append(" ".join(current))

        return chunks


def document_title(sections: list[Section], source: str) -> str:
    """The first heading of a document, or its file name without extension.

    Docling returns the document title as the first heading for PDFs, and as
    a title item (read as a heading) for DOCX, HTML and Markdown.
    """

    for section in sections:
        if section.heading.strip():
            return section.heading.strip()

    return Path(source).stem


def strip_context(document: str, title: str, heading: str) -> str:
    """The chunk text without the title and heading lines added by the
    chunker, for showing a passage to the user."""

    for prefix in (f"{title}\n{heading}\n\n", f"{title}\n\n", f"{heading}\n\n"):
        if prefix.strip() and document.startswith(prefix):
            return document[len(prefix):]

    return document


def chunking_id(
    strategy: str,
    breakpoint_percentile: int,
    window: int,
    include_title: bool = False,
) -> str:
    """Name a chunking configuration, for example in collection names."""

    name = strategy

    if strategy == "semantic":
        name = f"semantic-p{breakpoint_percentile}-w{window}"

    return f"{name}-ctx" if include_title else name


def build_chunker(
    strategy: str,
    embedder: Embedder,
    max_chunk_size: int,
    min_chunk_size: int,
    breakpoint_percentile: int = 90,
    window: int = 1,
    include_title: bool = False,
) -> Chunker:
    if strategy == "sentence":
        return SentenceChunker(
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
            include_title=include_title,
        )

    if strategy == "semantic":
        return SemanticChunker(
            embedder=embedder,
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
            breakpoint_percentile=breakpoint_percentile,
            window=window,
            include_title=include_title,
        )

    choices = " or ".join(f"'{name}'" for name in CHUNKING_STRATEGIES)
    raise ValueError(
        f"Unknown chunking strategy '{strategy}'. Use {choices}."
    )


def _length(sentences: list[str]) -> int:
    """Length of the sentences joined into one chunk."""

    return len(" ".join(sentences))


def _percentile(values: list[float], percentile: float) -> float:
    """Percentile with linear interpolation between the closest ranks."""

    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _cosine_similarity(vector1: list[float], vector2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vector1, vector2))

    magnitude1 = math.sqrt(sum(a * a for a in vector1))
    magnitude2 = math.sqrt(sum(b * b for b in vector2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)
