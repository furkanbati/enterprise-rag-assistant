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

    if _has_evidence(report):
        lines += _render_evidence(report)

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
            f"| Citation rate (answered questions) | "
            f"{_fmt(generation.citation_rate)} |",
            f"| Answers with invalid citations | "
            f"{generation.invalid_citation_answers} |",
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


def _has_evidence(report: EvaluationReport) -> bool:
    return any(
        value is not None
        for summary in report.strategies
        for value in summary.evidence_recall.values()
    ) or bool(report.missing_evidence)


def _render_evidence(report: EvaluationReport) -> list[str]:
    max_k = max(report.ks)
    lines = [
        "",
        "## Evidence Coverage",
        "",
        "Share of the labelled evidence sentences found in the top-k chunks. "
        "Unlike the page-level metrics above, this changes with chunking. "
        "Context chars is the text the top-k chunks send to the model; "
        "larger chunks raise recall by sending more.",
        "",
    ]

    lines += _table_header(
        ["Strategy"]
        + [f"Evidence@{k}" for k in report.ks]
        + [f"Context chars@{k}" for k in report.ks]
    )

    for summary in report.strategies:
        lines.append(
            _table_row(
                [f"`{summary.strategy}`"]
                + [_fmt(summary.evidence_recall[k]) for k in report.ks]
                + [f"{summary.mean_context_chars[k]:.0f}" for k in report.ks]
            )
        )

    results = [
        result
        for result in report.retrieval_results
        if result.evidence_recall[max_k] is not None
    ]
    sources = list(dict.fromkeys(result.source or "-" for result in results))

    if sources:
        lines += [
            "",
            f"### Evidence@{max_k} by Source",
            "",
        ]
        lines += _table_header(["Strategy"] + sources)

        for summary in report.strategies:
            cells = []

            for source in sources:
                values = [
                    result.evidence_recall[max_k]
                    for result in results
                    if result.strategy == summary.strategy
                    and (result.source or "-") == source
                ]
                cells.append(_fmt(sum(values) / len(values)))

            lines.append(_table_row([f"`{summary.strategy}`"] + cells))

    if report.missing_evidence:
        lines += [
            "",
            "## Missing Evidence",
            "",
            "These evidence sentences were not found in any indexed chunk, "
            "which points to a labelling or parsing problem.",
            "",
            *[
                f"- `{sample_id}`: {' '.join(sentence.split())}"
                for sample_id, sentence in report.missing_evidence
            ],
        ]

    return lines


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
