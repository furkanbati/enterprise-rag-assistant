import logging
from collections.abc import Iterator

from ollama import Client

from providers.base import close_stream

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


THINK_LEVELS = ("low", "medium", "high")


def parse_think(value: str | None) -> bool | str | None:
    """The OLLAMA_THINK setting: empty keeps the model's default, "true" or
    "false" turns thinking on or off, and "low", "medium" or "high" sets its
    level on models that support levels."""

    value = (value or "").strip().lower()

    if not value:
        return None

    if value in ("true", "false"):
        return value == "true"

    if value in THINK_LEVELS:
        return value

    raise ValueError(
        f"Invalid OLLAMA_THINK '{value}'. Use true, false, low, medium or high."
    )


class OllamaChatClient:
    """Generates chat completions using an Ollama chat model.

    ``think`` controls the reasoning of thinking models (such as qwen3.5):
    None leaves the model's default, False turns it off. A thinking model
    writes its reasoning before the answer, which on a CPU or a small GPU
    can take minutes and fill the context before the answer starts."""

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
        think: bool | str | None = None,
    ) -> None:
        self.client = Client(host=host)
        self.model = model
        self.think = think

    def complete(self, system: str, user: str) -> str:
        response = self.client.chat(
            model=self.model,
            messages=_messages(system, user),
            **self._options(),
        )

        return response.message.content

    def stream(self, system: str, user: str) -> Iterator[str]:
        parts = self.client.chat(
            model=self.model,
            messages=_messages(system, user),
            stream=True,
            **self._options(),
        )

        try:
            for part in parts:
                if part.message.content:
                    yield part.message.content
        finally:
            close_stream(parts)

    def _options(self) -> dict:
        # Sent only when set, so models without thinking get the same request
        # as before.
        return {} if self.think is None else {"think": self.think}


def _messages(system: str, user: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": system,
        },
        {
            "role": "user",
            "content": user,
        },
    ]
