from embedder import Embedder
from retriever import Retriever
from generator import Generator


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

    def run(self, question: str) -> str:
        logger.info("Processing question through RAG pipeline")
        
        query_embedding = self.embedder.embed(question)

        retrieved_chunks = self.retriever.search(query_embedding)

        answer = self.generator.generate(
            question=question,
            chunks=retrieved_chunks,
        )

        return answer