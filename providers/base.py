from typing import Protocol


class Embedder(Protocol):
    """Turns text into embedding vectors."""

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class ChatClient(Protocol):
    """Sends a system and a user message to a chat model and returns the reply."""

    def complete(self, system: str, user: str) -> str: ...
