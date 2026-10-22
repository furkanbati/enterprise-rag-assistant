import logging

from ollama import Client

logger = logging.getLogger(__name__)


class OllamaEmbedder:
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


class OllamaChatClient:
    """Generates chat completions using an Ollama chat model."""

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
    ) -> None:
        self.client = Client(host=host)
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": user,
                },
            ],
        )

        return response.message.content
