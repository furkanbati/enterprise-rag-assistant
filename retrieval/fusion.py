from models import RetrievedChunk
from copy import deepcopy

class ReciprocalRankFusion:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        vector_chunks: list[RetrievedChunk],
        keyword_chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        scores: dict[tuple[str, int, int], RetrievedChunk] = {}

        self._update_scores(scores, vector_chunks)
        self._update_scores(scores, keyword_chunks)

        return sorted(
            scores.values(),
            key=lambda chunk: chunk.fusion_score or 0,
            reverse=True,
        )

    def _update_scores(
        self,
        scores: dict[tuple[str, int, int], RetrievedChunk],
        chunks: list[RetrievedChunk],
    ) -> None:
        for rank, chunk in enumerate(chunks, start=1):
            key = (
                chunk.metadata.source,
                chunk.metadata.page,
                chunk.metadata.chunk,
            )

            score = 1 / (self.k + rank)

            if key not in scores:
                new_chunk = deepcopy(chunk)
                new_chunk.fusion_score = score
                scores[key] = new_chunk
            else:
                existing = scores[key]

                existing.fusion_score += score

                if chunk.vector_score is not None:
                    existing.vector_score = chunk.vector_score

                if chunk.keyword_score is not None:
                    existing.keyword_score = chunk.keyword_score