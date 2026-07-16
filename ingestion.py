import logging
from pathlib import Path

import fitz

from embedder import Embedder
from models import ChunkMetadata, Page
from vector_store import VectorStore

logger = logging.getLogger(__name__)


class Ingestion:
    """Processes PDF documents and stores their embeddings in the vector database."""

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
        pages = self._extract_text(pdf_path)

        documents, metadatas = self._chunk(
            pages=pages,
            source=Path(pdf_path).name,
        )

        logger.info("Extracted %d document chunks", len(documents))

        embeddings = self.embedder.embed_batch(documents)

        self.vector_store.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Stored %d document chunks", len(documents))

    def _extract_text(self, pdf_path: str) -> list[Page]:
        document = fitz.open(pdf_path)

        pages: list[Page] = []

        for page_number, page in enumerate(document, start=1):
            pages.append(
                Page(
                    page=page_number,
                    text=page.get_text(),
                )
            )

        document.close()

        return pages

    def _chunk(
        self,
        pages: list[Page],
        source: str,
    ) -> tuple[list[str], list[ChunkMetadata]]:
        documents: list[str] = []
        metadatas: list[ChunkMetadata] = []

        chunk_id = 0

        for page in pages:
            start = 0

            while start < len(page.text):
                end = start + self.chunk_size

                documents.append(page.text[start:end])

                metadatas.append(
                    ChunkMetadata(
                        source=source,
                        page=page.page,
                        chunk=chunk_id,
                    )
                )

                chunk_id += 1
                start = end - self.overlap

        return documents, metadatas