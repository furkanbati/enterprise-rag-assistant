import logging
from collections.abc import Iterator

from generator import Generator
from models import PipelineResult, RetrievedChunk
from providers.base import Embedder
from retrieval.retriever import Retriever

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

        retrieved_chunks = self.retrieve(question)

        answer = self.generator.generate(
            question=question,
            chunks=retrieved_chunks,
        )

        return PipelineResult(
            answer=answer,
            chunks=retrieved_chunks,
        )

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        query_embedding = self.embedder.embed(question)

        return self.retriever.search(
            query=question,
            embedding=query_embedding,
        )

    def stream(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> Iterator[str]:
        """Yield the answer to a question from already retrieved chunks."""

        return self.generator.stream(
            question=question,
            chunks=chunks,
        )
