import json
from dataclasses import asdict
from pathlib import Path

from evaluation.evaluator import EvaluationReport


def write_reports(
    report: EvaluationReport,
    output_dir: str | Path,
    metadata: dict,
) -> tuple[Path, Path]:
    """Write the evaluation report as JSON and Markdown."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "report.json"
    markdown_path = output_dir / "report.md"

    json_path.write_text(
        json.dumps(
            {"metadata": metadata, **asdict(report)},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    markdown_path.write_text(
        render_markdown(report, metadata),
        encoding="utf-8",
    )

    return json_path, markdown_path


def render_markdown(report: EvaluationReport, metadata: dict) -> str:
    max_k = max(report.ks)
    lines = [
        "# RAG Evaluation Report",
        "",
        *[f"- **{key}:** {value}" for key, value in metadata.items()],
        f"- **Questions:** {report.num_samples} "
        f"({report.num_answerable} answerable, "
        f"{report.num_samples - report.num_answerable} unanswerable)",
        "",
        "## Retrieval",
        "",
        "Relevance is judged at page level against the labelled dataset. "
        "Unanswerable questions are excluded from retrieval metrics.",
        "",
    ]

    header = (
        ["Strategy"]
        + [f"Hit@{k}" for k in report.ks]
        + [f"Recall@{k}" for k in report.ks]
        + [f"MRR@{max_k}", "Latency (ms)"]
    )
    lines += _table_header(header)

    for summary in report.strategies:
        lines.append(
            _table_row(
                [f"`{summary.strategy}`"]
                + [_fmt(summary.hit[k]) for k in report.ks]
                + [_fmt(summary.recall[k]) for k in report.ks]
                + [_fmt(summary.mrr), f"{summary.mean_latency_ms:.0f}"]
            )
        )

    if report.generation is not None:
        generation = report.generation
        lines += [
            "",
            "## Answer Generation",
            "",
            f"Answers generated with `{generation.strategy}` "
            f"using the top {generation.top_k} chunks.",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Keyword recall (answerable) | "
            f"{_fmt(generation.mean_keyword_recall)} |",
            f"| Answer rate (answerable) | {_fmt(generation.answer_rate)} |",
            f"| Abstention rate (unanswerable) | "
            f"{_fmt(generation.abstention_rate)} |",
            f"| Mean generation latency (ms) | "
            f"{generation.mean_latency_ms:.0f} |",
        ]

    lines += [
        "",
        "## Per-question Reciprocal Rank",
        "",
    ]

    strategy_names = [summary.strategy for summary in report.strategies]
    lines += _table_header(["Question"] + strategy_names)

    sample_ids = list(
        dict.fromkeys(result.sample_id for result in report.retrieval_results)
    )
    results_by_key = {
        (result.sample_id, result.strategy): result
        for result in report.retrieval_results
    }

    for sample_id in sample_ids:
        lines.append(
            _table_row(
                [sample_id]
                + [
                    _fmt(results_by_key[(sample_id, name)].reciprocal_rank)
                    for name in strategy_names
                ]
            )
        )

    if report.answer_results:
        lines += [
            "",
            "## Generated Answers",
            "",
        ]

        for result in report.answer_results:
            score = (
                f"keyword recall {_fmt(result.keyword_recall)}"
                if result.keyword_recall is not None
                else "unanswerable"
            )
            abstained = "abstained" if result.abstained else "answered"

            lines += [
                f"**{result.sample_id}. {result.question}** "
                f"_({score}, {abstained})_",
                "",
                _blockquote(result.answer),
                "",
            ]

    return "\n".join(lines).rstrip() + "\n"


def _table_header(columns: list[str]) -> list[str]:
    return [
        _table_row(columns),
        _table_row(["---"] * len(columns)),
    ]


def _table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _blockquote(text: str) -> str:
    return "\n".join(
        f"> {line}" if line else ">"
        for line in text.strip().splitlines()
    )
