from ollama import Client
import logging

logger = logging.getLogger(__name__)

class Embedder:
    """Generates embeddings using an Ollama embedding model."""
    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
    ) -> None:
        self.client = Client(host=host)
        self.model = model

    def embed(self, text: str) -> list[float]:
        response = self.client.embed(
            model=self.model,
            input=text,
        )

        return response.embeddings[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        logger.info("Generating embeddings for %d document chunks", len(texts))
        response = self.client.embed(
            model=self.model,
            input=texts,
        )

        return response.embeddings