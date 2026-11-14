"""Compare retrieval configurations with RAGAS metrics.

Every test question is answered with each requested configuration, then a
judge model scores faithfulness, answer relevancy, context precision and
context recall. Usage (inside the eval container, see docker-compose.yml):

    python -m evaluation.ragas_eval --config hybrid_rerank
    python -m evaluation.ragas_eval --config all --ingest
    python -m evaluation.ragas_eval --config vector --limit 5 --judge-provider ollama
"""

import argparse
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import (
    CHAT_MODEL,
    EMBED_MODEL,
    EMBED_PROVIDER,
    FINAL_TOP_K,
    JUDGE_MODEL,
    JUDGE_PROVIDER,
    LLM_PROVIDER,
    RAGAS_EMBED_MODEL,
    RAGAS_EMBED_PROVIDER,
    RERANK_MODEL,
    RETRIEVAL_TOP_K,
)
from evaluation.components import (
    RetrievalComponents,
    build_components,
    build_ingestion,
    build_strategies,
)
from evaluation.ragas_eval.dataset import LANGUAGES, RagasSample, load_ragas_dataset
from evaluation.ragas_eval.report import write_config_results, write_summary
from evaluation.ragas_eval.runner import (
    CONFIGS,
    METRICS,
    check_judge,
    collect_records,
    score_records,
    summarize,
)
from generator import Generator
from providers.factory import build_chat_client

PACKAGE_DIR = Path(__file__).parent
DEFAULT_DATASET = PACKAGE_DIR.parent / "datasets" / "ragas_testset.jsonl"
DEFAULT_OUTPUT = PACKAGE_DIR.parent / "results" / "ragas"

logger = logging.getLogger("evaluation.ragas_eval")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m evaluation.ragas_eval",
        description="Compare retrieval configurations with RAGAS metrics.",
    )
    parser.add_argument(
        "--config",
        choices=[*CONFIGS, "all"],
        default="hybrid_rerank",
        help=(
            "Retrieval configuration: vector (vector search only), hybrid "
            "(vector + BM25 with RRF), hybrid_rerank (hybrid + cross-encoder, "
            "the production setup) or all. Default: hybrid_rerank."
        ),
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        choices=METRICS,
        default=list(METRICS),
        help=(
            "Metrics to compute (default: all four). Context precision and "
            "context recall grade retrieval only, so a run that changes only "
            "the chat model can skip them: --metrics faithfulness "
            "answer_relevancy needs about half the judge calls."
        ),
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--limit",
        type=int,
        help="Evaluate only the first N questions, for a quick check.",
    )
    parser.add_argument(
        "--language",
        choices=LANGUAGES,
        help="Evaluate only the questions in this language.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=FINAL_TOP_K,
        help=f"Passages given to the model (default FINAL_TOP_K = {FINAL_TOP_K}).",
    )
    parser.add_argument(
        "--judge-provider",
        default=JUDGE_PROVIDER,
        help=f"Judge LLM provider (default JUDGE_PROVIDER = {JUDGE_PROVIDER}).",
    )
    parser.add_argument(
        "--judge-model",
        help="Judge LLM (default JUDGE_MODEL, or the provider's default model).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        help=(
            "Judge requests in flight at once. Default: 4 for OpenAI, "
            "1 for Ollama, which answers one request at a time on a CPU."
        ),
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help=(
            "Index the dataset's documents that are not indexed yet, from "
            "--documents-dir, before evaluating."
        ),
    )
    parser.add_argument(
        "--documents-dir",
        type=Path,
        default=Path("."),
        help="Where --ingest looks for the documents (default: current directory).",
    )
    parser.add_argument("--rerank-model", default=RERANK_MODEL)
    parser.add_argument("--verbose", action="store_true")

    return parser.parse_args(argv)


def select_samples(
    samples: list[RagasSample],
    language: str | None,
    limit: int | None,
) -> list[RagasSample]:
    if language:
        samples = [sample for sample in samples if sample.language == language]

    if limit is not None:
        samples = samples[:limit]

    return samples


def select_metrics(metrics: dict, names: list[str]) -> dict:
    """The requested metrics, in the order of METRICS, without duplicates."""

    return {name: metrics[name] for name in METRICS if name in names}


def resolve_judge_model(provider: str, model: str | None) -> str:
    """The judge model: the flag, else JUDGE_MODEL when it belongs to the
    chosen provider, else that provider's default."""

    if model:
        return model

    if provider == JUDGE_PROVIDER:
        return JUDGE_MODEL

    return {"ollama": "llama3", "openai": "gpt-6.1-sol"}.get(provider, JUDGE_MODEL)


def ensure_documents_indexed(
    samples: list[RagasSample],
    components: RetrievalComponents,
    ingest: bool,
    documents_dir: Path,
) -> None:
    """Stop with a clear message, or index them with --ingest, when the
    documents the questions are about are not in the collection."""

    indexed = set(components.vector_store.list_sources())
    missing = sorted({sample.source for sample in samples} - indexed)

    if not missing:
        return

    if not ingest:
        raise SystemExit(
            "These documents are not indexed: "
            + ", ".join(missing)
            + ". Upload them through POST /upload, or rerun with --ingest "
            "(see evaluation/datasets/README.md for download links)."
        )

    not_found = [name for name in missing if not (documents_dir / name).is_file()]

    if not_found:
        raise SystemExit(
            f"Cannot index {', '.join(not_found)}: not found in {documents_dir}. "
            "See evaluation/datasets/README.md for download links."
        )

    ingestion = build_ingestion(components)

    for name in missing:
        logger.info("Indexing %s", name)
        result = ingestion.ingest(str(documents_dir / name))
        logger.info("Indexed %s: %d chunks", name, result.chunks)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    logger.setLevel(logging.INFO)

    samples = select_samples(
        load_ragas_dataset(args.dataset),
        language=args.language,
        limit=args.limit,
    )

    if not samples:
        raise SystemExit("No questions selected.")

    configs = list(CONFIGS) if args.config == "all" else [args.config]
    judge_model = resolve_judge_model(args.judge_provider, args.judge_model)
    concurrency = args.concurrency or (4 if args.judge_provider == "openai" else 1)

    # Build the judge first, so a missing key fails before any answering.
    from evaluation.ragas_eval.metrics import build_ragas_metrics

    all_metrics = build_ragas_metrics(
        judge_provider=args.judge_provider,
        judge_model=judge_model,
        embed_provider=RAGAS_EMBED_PROVIDER,
        embed_model=RAGAS_EMBED_MODEL,
    )
    metrics = select_metrics(all_metrics, args.metrics)

    # One event loop for every judge call: the async clients keep their
    # connections, which belong to the loop that opened them, and fail with
    # "Event loop is closed" in a new loop.
    loop = asyncio.new_event_loop()

    try:
        _run(args, samples, configs, judge_model, concurrency, metrics, loop)
    finally:
        loop.close()


def _run(args, samples, configs, judge_model, concurrency, metrics, loop) -> None:
    try:
        loop.run_until_complete(check_judge(metrics))
    except RuntimeError as e:
        raise SystemExit(str(e)) from e

    components = build_components()
    ensure_documents_indexed(
        samples,
        components,
        ingest=args.ingest,
        documents_dir=args.documents_dir,
    )

    strategies = build_strategies(
        components,
        rerank_model=args.rerank_model,
        names=[CONFIGS[config] for config in configs],
    )
    generator = Generator(
        client=build_chat_client(provider=LLM_PROVIDER, model=CHAT_MODEL)
    )

    metadata = {
        "Date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "Dataset": f"{args.dataset.name} ({len(samples)} questions)",
        "Chat model": f"{LLM_PROVIDER}/{CHAT_MODEL}",
        "Judge model": f"{args.judge_provider}/{judge_model}",
        "Judge embeddings": f"{RAGAS_EMBED_PROVIDER}/{RAGAS_EMBED_MODEL}",
        "Retrieval embeddings": f"{EMBED_PROVIDER}/{EMBED_MODEL}",
        "Chunking": components.chunking,
        "Reranker": args.rerank_model,
        "Passages per answer": args.top_k,
        "Candidates per retriever": RETRIEVAL_TOP_K,
    }

    for config in configs:
        logger.info("[%s] answering %d questions", config, len(samples))

        records = collect_records(
            samples,
            strategy=strategies[CONFIGS[config]],
            embedder=components.embedder,
            generator=generator,
            top_k=args.top_k,
            on_progress=lambda done, total, config=config: logger.info(
                "[%s] answered %d/%d", config, done, total
            ),
        )

        logger.info("[%s] scoring with %s/%s", config, args.judge_provider, judge_model)
        loop.run_until_complete(
            score_records(records, metrics, concurrency=concurrency)
        )

        summary = summarize(config, records, metric_names=tuple(metrics))
        json_path, csv_path = write_config_results(
            args.output, summary, records, metadata
        )
        logger.info("[%s] results written to %s and %s", config, json_path, csv_path)

    summary_path = write_summary(args.output)

    print(summary_path.read_text(encoding="utf-8"))
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
