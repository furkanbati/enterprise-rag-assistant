from embedder import Embedder
from retriever import Retriever
from generator import Generator


class Pipeline:
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
        query_embedding = self.embedder.embed(question)

        documents = self.retriever.search(query_embedding)

        answer = self.generator.generate(
            question=question,
            documents=documents,
        )

        return answer