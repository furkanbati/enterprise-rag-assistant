import logging
from pathlib import Path

from chunking import Chunker
from document_parser import DocumentParser
from models import IngestionResult
from providers.base import Embedder
from vector_store import VectorStore
from retrieval.keyword_search import KeywordSearch
logger = logging.getLogger(__name__)


class Ingestion:
    """Processes documents and stores their embeddings in the vector database."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        chunker: Chunker,
        keyword_search: KeywordSearch,
        ocr_engine: str = "rapidocr",
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunker = chunker
        self.keyword_search = keyword_search
        self.document_parser = DocumentParser(ocr_engine)

    def ingest(self, path: str) -> IngestionResult:
        """Index a document, replacing an earlier version with the same name.

        The new version is parsed, chunked and embedded before the old one is
        deleted, so a document that fails to process leaves the indexed
        version untouched.
        """

        source = Path(path).name
        sections = self.document_parser.parse(path)

        documents, metadatas = self.chunker.chunk(
            sections=sections,
            source=source,
        )

        if not documents:
            raise ValueError(
                f"No text could be extracted from {source}."
            )

        logger.info("Extracted %d document chunks", len(documents))

        embeddings = self.embedder.embed_batch(documents)

        replaced = self.vector_store.delete_source(source) > 0

        self.vector_store.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        self.keyword_search.rebuild()
        logger.info("Stored %d document chunks", len(documents))

        return IngestionResult(
            source=source,
            chunks=len(documents),
            replaced=replaced,
        )
