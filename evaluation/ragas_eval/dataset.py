import json
from dataclasses import dataclass
from pathlib import Path

LANGUAGES = ("en", "tr")


@dataclass
class RagasSample:
    """A test question with the reference answer RAGAS compares against.

    ``reference`` is the ground truth: context recall checks that the
    retrieved passages contain it, and context precision ranks the passages
    by whether they help to reach it. ``source`` names the document that
    contains the answer, so the run can check that it is indexed.
    """

    id: str
    question: str
    reference: str
    source: str
    language: str = "en"


def load_ragas_dataset(path: str | Path) -> list[RagasSample]:
    """Load RAGAS test questions from a JSON Lines file."""

    samples: list[RagasSample] = []
    seen: set[str] = set()

    with open(path, encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                sample = RagasSample(**json.loads(line))
            except (json.JSONDecodeError, TypeError) as e:
                raise ValueError(
                    f"Invalid RAGAS sample on line {line_number}: {e}"
                ) from e

            if not sample.question.strip() or not sample.reference.strip():
                raise ValueError(
                    f"Sample '{sample.id}' needs a question and a reference."
                )

            if sample.language not in LANGUAGES:
                raise ValueError(
                    f"Sample '{sample.id}' has unknown language "
                    f"'{sample.language}'; use one of {', '.join(LANGUAGES)}."
                )

            if sample.id in seen:
                raise ValueError(f"Duplicate sample id '{sample.id}'.")

            seen.add(sample.id)
            samples.append(sample)

    return samples
