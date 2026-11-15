
from sentence_transformers import CrossEncoder

from models import RetrievedChunk


class CrossEncoderReranker:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model: CrossEncoder | None = None

    def load(self) -> None:
        """Load the model now instead of on the first rerank. The first load
        downloads it from Hugging Face; later loads read the local cache."""

        if self.model is None:
            self.model = CrossEncoder(self.model_name)

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        self.load()

        pairs = [
            (question, chunk.document)
            for chunk in chunks
        ]

        scores = self.model.predict(
            pairs,
            batch_size=16,
        )

        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)

        chunks.sort(
            key=lambda chunk: chunk.rerank_score,
            reverse=True,
        )

        return chunks[:top_k]
