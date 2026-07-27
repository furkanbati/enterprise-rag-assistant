import re
import math

from embedder import Embedder
from models import ChunkMetadata, Page


class SemanticChunker:
    def __init__(
        self,
        embedder: Embedder,
        chunk_size: int,
        min_chunk_size: int,
        similarity_threshold: float,
    ) -> None:
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
        self.similarity_threshold = similarity_threshold

    def chunk(
        self,
        pages: list[Page],
        source: str,
    ) -> tuple[list[str], list[ChunkMetadata]]:
        """
        Main entry point for document chunking.
        """

        documents: list[str] = []
        metadatas: list[ChunkMetadata] = []

        chunk_id = 0

        for page in pages:
            text = self._clean_text(page.text)

            if not text:
                continue

            sentences = self._split_sentences(text)

            similarities = self._calculate_similarities(sentences)

            chunks = self._build_chunks(
                sentences=sentences,
                similarities=similarities,
            )

            for chunk in chunks:
                documents.append(chunk)

                metadatas.append(
                    ChunkMetadata(
                        source=source,
                        page=page.number,
                        chunk=chunk_id,
                    )
                )

                chunk_id += 1

        return documents, metadatas

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

    def _build_chunks(
        self,
        sentences: list[str],
        similarities: list[float],
    ) -> list[str]:
        """
        Build semantic chunks using sentence similarity.

        A new chunk is started when:
        - similarity drops below the configured threshold
        - maximum chunk size would be exceeded
        """

        if not sentences:
            return []

        chunks: list[str] = []

        current_chunk = [sentences[0]]
        current_length = len(sentences[0])

        for i in range(1, len(sentences)):
            sentence = sentences[i]
            similarity = similarities[i - 1]

            should_split = (
                similarity < self.similarity_threshold
                and current_length >= self.min_chunk_size
            ) or (
                current_length + len(sentence) > self.chunk_size
            )

            if should_split:
                chunks.append(" ".join(current_chunk))

                current_chunk = [sentence]
                current_length = len(sentence)

            else:
                current_chunk.append(sentence)
                current_length += len(sentence)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks



    def _calculate_similarities(
        self,
        sentences: list[str],
    ) -> list[float]:
        """
        Calculate cosine similarity between consecutive sentence embeddings.
        """

        if len(sentences) < 2:
            return []

        embeddings = self.embedder.embed_batch(sentences)

        similarities: list[float] = []

        for i in range(len(embeddings) - 1):
            similarities.append(
                self._cosine_similarity(
                    embeddings[i],
                    embeddings[i + 1],
                )
            )

        return similarities


    def _cosine_similarity(
        self,
        vector1: list[float],
        vector2: list[float],
    ) -> float:
        """
        Compute cosine similarity between two vectors.
        """

        dot_product = sum(a * b for a, b in zip(vector1, vector2))

        magnitude1 = math.sqrt(sum(a * a for a in vector1))
        magnitude2 = math.sqrt(sum(b * b for b in vector2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)