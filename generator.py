from ollama import Client


class Generator:

    """Generates answers from retrieved document chunks using an Ollama chat model."""

    SYSTEM_PROMPT = """
You are a helpful AI assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context, say that you don't know.

Be concise and accurate.
"""

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
    ) -> None:
        self.client = Client(host=host)
        self.model = model

    def generate(
        self,
        question: str,
        documents: list[str],
    ) -> str:
        logger.info(
        "Generating response using %d retrieved document chunks",
        len(documents),
        )
        prompt = self._build_prompt(question, documents)

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.message.content

    def _build_prompt(
        self,
        question: str,
        documents: list[str],
    ) -> str:
        context = "\n\n".join(documents)

        return (
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )