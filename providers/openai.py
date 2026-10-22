import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIEmbedder:
    """Generates embeddings using an OpenAI-compatible embeddings endpoint."""

    # Keeps each request well below the API's limit on inputs per request.
    BATCH_SIZE = 256

    def __init__(
        self,
        client: OpenAI,
        model: str,
    ) -> None:
        self.client = client
        self.model = model

    def embed(self, text: str) -> list[float]:
        return self._request([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        logger.info("Generating embeddings for %d document chunks", len(texts))

        embeddings: list[list[float]] = []

        for start in range(0, len(texts), self.BATCH_SIZE):
            embeddings.extend(
                self._request(texts[start:start + self.BATCH_SIZE])
            )

        return embeddings

    def _request(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        return [
            item.embedding
            for item in sorted(response.data, key=lambda item: item.index)
        ]


class OpenAIChatClient:
    """Generates chat completions using an OpenAI-compatible chat endpoint."""

    def __init__(
        self,
        client: OpenAI,
        model: str,
        reasoning_effort: str | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.reasoning_effort = reasoning_effort

    def complete(self, system: str, user: str) -> str:
        options = {}

        if self.reasoning_effort:
            options["reasoning_effort"] = self.reasoning_effort

        response = self.client.chat.completions.create(
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
            **options,
        )

        return response.choices[0].message.content or ""
