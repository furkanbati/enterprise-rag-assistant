from embedder import Embedder
from retriever import Retriever
from generator import Generator
from models import PipelineResult, RetrievedChunk
import logging

logger = logging.getLogger(__name__)

class Pipeline:
    """Coordinates the RAG workflow from query embedding to answer generation."""
    def __init__(
        self,
        embedder: Embedder,
        retriever: Retriever,
        generator: Generator,
    ) -> None:
        self.embedder = embedder
        self.retriever = retriever
        self.generator = generator

    def run(self, question: str) -> PipelineResult:
        logger.info("Processing question through RAG pipeline")

        query_embedding = self.embedder.embed(question)

        retrieved_chunks = self.retriever.search(query_embedding)

        answer = self.generator.generate(
            question=question,
            chunks=retrieved_chunks,
        )

        return PipelineResult(
            answer=answer,
            chunks=retrieved_chunks,
        )