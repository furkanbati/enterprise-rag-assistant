import re
from typing import Protocol

from providers.base import Embedder
from models import ChunkMetadata, Section

CHUNKING_STRATEGIES = ("sentence",)


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
    its section heading.
    """

    def __init__(
        self,
        max_chunk_size: int,
        min_chunk_size: int,
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(
        self,
        sections: list[Section],
        source: str,
    ) -> tuple[list[str], list[ChunkMetadata]]:
        """
        Main entry point for document chunking.
        """

        documents: list[str] = []
        metadatas: list[ChunkMetadata] = []

        chunk_id = 0

        for section in sections:
            text = self._clean_text(section.text)

            if not text:
                continue

            sentences = self._split_sentences(text)

            for chunk in self._split(sentences):
                document = chunk
                if section.heading:
                    document = f"{section.heading}\n\n{chunk}"
                documents.append(document)

                metadatas.append(
                    ChunkMetadata(
                        source=source,
                        page=section.page,
                        chunk=chunk_id,
                        heading=section.heading,
                        level=section.level,
                    )
                )

                chunk_id += 1

        return documents, metadatas

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


def build_chunker(
    strategy: str,
    embedder: Embedder,
    max_chunk_size: int,
    min_chunk_size: int,
) -> Chunker:
    if strategy == "sentence":
        return SentenceChunker(
            max_chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
        )

    choices = " or ".join(f"'{name}'" for name in CHUNKING_STRATEGIES)
    raise ValueError(
        f"Unknown chunking strategy '{strategy}'. Use {choices}."
    )
