import logging
from pathlib import Path

from chunking import SemanticChunker
from document_parser import DocumentParser
from embedder import Embedder
from vector_store import VectorStore
from retrieval.keyword_search import KeywordSearch
logger = logging.getLogger(__name__)


class Ingestion:
    """Processes PDF documents and stores their embeddings in the vector database."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        chunker: SemanticChunker,
        keyword_search: KeywordSearch,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.chunker = chunker
        self.keyword_search = keyword_search
        self.document_parser = DocumentParser()

    def ingest(self, pdf_path: str) -> None:
        sections = self.document_parser.parse(pdf_path)

        documents, metadatas = self.chunker.chunk(
            sections=sections,
            source=Path(pdf_path).name,
        )

        logger.info("Extracted %d document chunks", len(documents))

        embeddings = self.embedder.embed_batch(documents)

        self.vector_store.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        self.keyword_search.rebuild()
        logger.info("Stored %d document chunks", len(documents))