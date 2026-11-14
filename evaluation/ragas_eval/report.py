"""Write RAGAS results per configuration and a combined Markdown summary."""

import csv
import json
from dataclasses import asdict
from pathlib import Path

from evaluation.ragas_eval.runner import (
    CONFIG_DESCRIPTIONS,
    CONFIGS,
    METRICS,
    ConfigSummary,
    RagRecord,
)

METRIC_TITLES = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer relevancy",
    "context_precision": "Context precision",
    "context_recall": "Context recall",
}

LANGUAGE_TITLES = {"en": "English", "tr": "Turkish"}


def write_config_results(
    output_dir: str | Path,
    summary: ConfigSummary,
    records: list[RagRecord],
    metadata: dict,
) -> tuple[Path, Path]:
    """Write one configuration's results: JSON with everything, and a CSV
    with one row per question for a spreadsheet."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"{summary.config}.json"
    csv_path = output_dir / f"{summary.config}.csv"

    json_path.write_text(
        json.dumps(
            {
                "metadata": metadata,
                "summary": asdict(summary),
                "records": [asdict(record) for record in records],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id",
            "language",
            "question",
            *METRICS,
            "sources",
            "answer",
            "errors",
        ])

        for record in records:
            writer.writerow([
                record.sample_id,
                record.language,
                record.question,
                *(_csv_number(record.scores.get(name)) for name in METRICS),
                "; ".join(record.sources),
                record.answer,
                "; ".join(f"{k}: {v}" for k, v in record.errors.items()),
            ])

    return json_path, csv_path


def write_summary(output_dir: str | Path) -> Path:
    """Combine every configuration result in the directory into summary.md,
    so configurations run one at a time end up in one table."""

    output_dir = Path(output_dir)
    results = load_results(output_dir)

    path = output_dir / "summary.md"
    path.write_text(render_summary(results), encoding="utf-8")

    return path


def load_results(output_dir: Path) -> list[dict]:
    """The saved configuration results, in the order of CONFIGS."""

    results = []

    for config in CONFIGS:
        path = output_dir / f"{config}.json"

        if path.exists():
            results.append(json.loads(path.read_text(encoding="utf-8")))

    return results


def render_summary(results: list[dict]) -> str:
    if not results:
        return "# RAGAS Evaluation\n\nNo results yet.\n"

    summaries = [result["summary"] for result in results]
    # Bold the best value of each column, when there is something to compare.
    best = {
        name: max(
            (s["scores"][name] for s in summaries if s["scores"][name] is not None),
            default=None,
        ) if len(summaries) > 1 else None
        for name in METRICS
    }

    lines = [
        "# RAGAS Evaluation",
        "",
        "| Configuration | Retrieval | "
        + " | ".join(METRIC_TITLES[name] for name in METRICS)
        + " |",
        "|---|---|" + "---|" * len(METRICS),
    ]

    for summary in summaries:
        cells = [
            _score_cell(summary["scores"][name], best[name])
            for name in METRICS
        ]
        lines.append(
            f"| `{summary['config']}` "
            f"| {CONFIG_DESCRIPTIONS.get(summary['config'], summary['strategy'])} | "
            + " | ".join(cells)
            + " |"
        )

    languages = sorted({
        language
        for summary in summaries
        for language in summary["scores_by_language"]
    })

    if len(languages) > 1:
        lines += [
            "",
            "### By language",
            "",
            "| Configuration | Language | "
            + " | ".join(METRIC_TITLES[name] for name in METRICS)
            + " |",
            "|---|---|" + "---|" * len(METRICS),
        ]

        for summary in summaries:
            for language in languages:
                scores = summary["scores_by_language"].get(language)

                if scores is None:
                    continue

                lines.append(
                    f"| `{summary['config']}` "
                    f"| {LANGUAGE_TITLES.get(language, language)} | "
                    + " | ".join(_score_cell(scores[name]) for name in METRICS)
                    + " |"
                )

    lines += ["", "### Run details", ""]
    lines += _run_details(results)

    unscored = [
        f"`{summary['config']}`: "
        + ", ".join(
            f"{METRIC_TITLES[name].lower()} {count}"
            for name, count in summary["unscored"].items()
            if count
        )
        for summary in summaries
        if any(summary["unscored"].values())
    ]

    if unscored:
        lines += [
            "",
            "Questions a metric could not score (the judge failed or returned "
            "no verdict) are left out of its mean:",
            "",
            *(f"- {line}" for line in unscored),
        ]

    lines += [
        "",
        "Scores range from 0 to 1, higher is better; the best value of each "
        "column is in bold. Per-question scores, answers and passages are in "
        "the JSON and CSV file of each configuration.",
        "",
    ]

    return "\n".join(lines)


def _run_details(results: list[dict]) -> list[str]:
    """Settings shared by all configurations once, and per configuration
    where they differ."""

    keys = list(results[0]["metadata"])
    lines = []

    for key in keys:
        values = [result["metadata"].get(key) for result in results]

        if all(value == values[0] for value in values):
            lines.append(f"- **{key}:** {values[0]}")
        else:
            per_config = ", ".join(
                f"`{result['summary']['config']}` {result['metadata'].get(key)}"
                for result in results
            )
            lines.append(f"- **{key}:** {per_config}")

    timings = ", ".join(
        f"`{s['config']}` {s['mean_retrieval_ms']:.0f} ms / "
        f"{s['mean_generation_ms'] / 1000:.1f} s"
        for s in (result["summary"] for result in results)
    )
    lines.append(f"- **Mean retrieval / generation time:** {timings}")

    return lines


def _score_cell(value: float | None, best: float | None = None) -> str:
    if value is None:
        return "n/a"

    text = f"{value:.3f}"

    if best is not None and round(value, 3) == round(best, 3):
        return f"**{text}**"

    return text


def _csv_number(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"
