import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EvalSample:
    """A single evaluation question with its ground-truth labels.

    Relevance is labelled at page level: a retrieved chunk is relevant when
    its page metadata matches one of ``relevant_pages``. Pages refer to the
    page metadata assigned during ingestion (the page where a section starts).

    ``evidence`` optionally lists sentences, copied verbatim from the parsed
    document, that contain the answer. Unlike pages, evidence is sensitive to
    how a document is chunked.
    """

    id: str
    question: str
    relevant_pages: list[int] = field(default_factory=list)
    expected_keywords: list[str] = field(default_factory=list)
    source: str | None = None
    answerable: bool = True
    evidence: list[str] = field(default_factory=list)


def load_dataset(path: str | Path) -> list[EvalSample]:
    """Load evaluation samples from a JSON Lines file."""

    samples: list[EvalSample] = []

    with open(path, encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                sample = EvalSample(**json.loads(line))
            except (json.JSONDecodeError, TypeError) as e:
                raise ValueError(
                    f"Invalid evaluation sample on line {line_number}: {e}"
                ) from e

            if sample.answerable and not sample.relevant_pages:
                raise ValueError(
                    f"Sample '{sample.id}' is answerable "
                    "but has no relevant_pages."
                )

            samples.append(sample)

    return samples
