import fitz

from embedder import Embedder
from vector_store import VectorStore


class Ingestion:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.overlap = overlap

    def ingest(self, pdf_path: str) -> None:
        text = self._extract_text(pdf_path)

        documents = self._chunk(text)

        embeddings = self.embedder.embed_batch(documents)

        self.vector_store.add(
            documents=documents,
            embeddings=embeddings,
        )

    def _extract_text(self, pdf_path: str) -> str:
        document = fitz.open(pdf_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        return text

    def _chunk(self, text: str) -> list[str]:
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            chunks.append(text[start:end])

            start = end - self.overlap

        return chunks