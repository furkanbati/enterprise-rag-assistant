import logging
from collections.abc import Iterator

from generator import Generator
from language import detect_language
from models import PipelineResult, RetrievedChunk
from providers.base import Embedder
from retrieval.retriever import Retriever

logger = logging.getLogger(__name__)


class Pipeline:
    """Coordinates the RAG workflow from query embedding to answer generation.

    The question's language picks the reranker (in the retriever) and the
    generator: ``language_generators`` maps a language to its generator, and
    languages without one use the default generator."""

    def __init__(
        self,
        embedder: Embedder,
        retriever: Retriever,
        generator: Generator,
        language_generators: dict[str, Generator] | None = None,
    ) -> None:
        self.embedder = embedder
        self.retriever = retriever
        self.generator = generator
        self.language_generators = language_generators or {}

    def generator_for(self, language: str) -> Generator:
        return self.language_generators.get(language, self.generator)

    def run(self, question: str) -> PipelineResult:
        logger.info("Processing question through RAG pipeline")

        retrieved_chunks = self.retrieve(question)

        answer = self.generator_for(detect_language(question)).generate(
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
            language=detect_language(question),
        )

    def stream(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> Iterator[str]:
        """Yield the answer to a question from already retrieved chunks."""

        return self.generator_for(detect_language(question)).stream(
            question=question,
            chunks=chunks,
        )
