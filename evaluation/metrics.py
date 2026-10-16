import re

from evaluation.dataset import EvalSample
from models import RetrievedChunk

ABSTENTION_PATTERNS = [
    r"\bdon'?t know\b",
    r"\bdo not know\b",
    r"\bnot (?:mentioned|provided|specified|stated|included|available)\b",
    r"\bcannot (?:be found|find|answer|determine)\b",
    r"\bcan'?t (?:find|answer|determine)\b",
    r"\bno (?:information|mention)\b",
    r"\bdoes not (?:mention|specify|provide|contain|say)\b",
    r"\bdoesn'?t (?:mention|specify|provide|contain|say)\b",
]


def is_relevant(chunk: RetrievedChunk, sample: EvalSample) -> bool:
    if sample.source is not None and chunk.metadata.source != sample.source:
        return False

    return chunk.metadata.page in sample.relevant_pages


def hit_at_k(
    chunks: list[RetrievedChunk],
    sample: EvalSample,
    k: int,
) -> float:
    """1.0 if any of the top-k chunks is relevant, otherwise 0.0."""

    return float(any(is_relevant(chunk, sample) for chunk in chunks[:k]))


def recall_at_k(
    chunks: list[RetrievedChunk],
    sample: EvalSample,
    k: int,
) -> float:
    """Fraction of relevant pages covered by the top-k chunks."""

    if not sample.relevant_pages:
        return 0.0

    found_pages = {
        chunk.metadata.page
        for chunk in chunks[:k]
        if is_relevant(chunk, sample)
    }

    return len(found_pages) / len(set(sample.relevant_pages))


def precision_at_k(
    chunks: list[RetrievedChunk],
    sample: EvalSample,
    k: int,
) -> float:
    """Fraction of the top-k chunks that are relevant."""

    top_chunks = chunks[:k]

    if not top_chunks:
        return 0.0

    relevant = sum(is_relevant(chunk, sample) for chunk in top_chunks)

    return relevant / len(top_chunks)


def reciprocal_rank(
    chunks: list[RetrievedChunk],
    sample: EvalSample,
) -> float:
    """1 / rank of the first relevant chunk, or 0.0 if none is relevant."""

    for rank, chunk in enumerate(chunks, start=1):
        if is_relevant(chunk, sample):
            return 1 / rank

    return 0.0


def keyword_recall(answer: str, keywords: list[str]) -> float:
    """Fraction of expected keywords that appear in the answer."""

    if not keywords:
        return 0.0

    normalized_answer = _normalize(answer)

    found = sum(
        _normalize(keyword) in normalized_answer
        for keyword in keywords
    )

    return found / len(keywords)


def is_abstention(answer: str) -> bool:
    """Detect whether the model declined to answer from the context."""

    normalized_answer = answer.lower().replace("’", "'")

    return any(
        re.search(pattern, normalized_answer)
        for pattern in ABSTENTION_PATTERNS
    )


def _normalize(text: str) -> str:
    text = text.lower().replace("-", " ")

    return re.sub(r"\s+", " ", text).strip()
