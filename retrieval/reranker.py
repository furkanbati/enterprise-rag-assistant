from sentence_transformers import CrossEncoder

from models import RetrievedChunk


class CrossEncoderReranker:
    def __init__(self, model_name: str):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

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