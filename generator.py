import logging
from collections.abc import Iterator

from models import RetrievedChunk
from providers.base import ChatClient

logger = logging.getLogger(__name__)


class Generator:
    """Generates answers from retrieved document chunks using a chat model."""

    SYSTEM_PROMPT = """
You are a helpful AI assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context, say that you don't know.

After each statement, cite the passages that support it with their numbers in
square brackets, for example [1] or [1][3]. Only cite numbers that appear in
the context.

Be concise and accurate.
"""

    def __init__(
        self,
        client: ChatClient,
    ) -> None:
        self.client = client

    def generate(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> str:

        prompt = self._build_prompt(
            question=question,
            chunks=chunks,
        )

        return self.client.complete(
            system=self.SYSTEM_PROMPT,
            user=prompt,
        )

    def stream(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> Iterator[str]:
        """Yield the answer in pieces as the model generates it."""

        prompt = self._build_prompt(
            question=question,
            chunks=chunks,
        )

        return self.client.stream(
            system=self.SYSTEM_PROMPT,
            user=prompt,
        )

    def _build_prompt(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> str:
        # Passages are numbered in the order of the returned sources, so
        # citation [n] refers to the n-th source.
        context = "\n\n".join(
            f"[{number}] {chunk.metadata.source}, page {chunk.metadata.page}\n"
            f"{chunk.document}"
            for number, chunk in enumerate(chunks, start=1)
        )

        return (
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )
