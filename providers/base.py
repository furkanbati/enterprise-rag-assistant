from collections.abc import Iterator
from typing import Protocol


class Embedder(Protocol):
    """Turns text into embedding vectors."""

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class ChatClient(Protocol):
    """Sends a system and a user message to a chat model and returns the reply."""

    def complete(self, system: str, user: str) -> str: ...

    def stream(self, system: str, user: str) -> Iterator[str]:
        """Yield the reply in pieces as the model generates it."""
        ...


def close_stream(stream: object) -> None:
    """Close a provider's response stream, if it can be closed, so that its
    HTTP connection is released as soon as the reader stops (for example
    when the client disconnects) instead of when it is garbage-collected."""

    close = getattr(stream, "close", None)

    if callable(close):
        close()
