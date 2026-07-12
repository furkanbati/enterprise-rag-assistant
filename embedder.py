from ollama import Client


class Embedder:
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
        response = self.client.embed(
            model=self.model,
            input=texts,
        )

        return response.embeddings