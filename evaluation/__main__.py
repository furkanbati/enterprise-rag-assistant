"""Evaluate retrieval and answer quality against a labelled dataset.

Usage (inside the API container):

    python -m evaluation
    python -m evaluation --generate
    python -m evaluation --ks 1 3 5 --output evaluation/results
"""

import argparse
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
    RERANK_MODEL,
    RETRIEVAL_TOP_K,
)
from evaluation import metrics
from evaluation.components import build_components, build_strategies
from evaluation.dataset import load_dataset
from evaluation.evaluator import Evaluator
from evaluation.report import write_reports
from generator import Generator
from evaluation.judge import AnswerJudge
from providers.factory import build_chat_client

DEFAULT_DATASET = Path(__file__).parent / "datasets" / "nist_ai_rmf.jsonl"
DEFAULT_OUTPUT = Path(__file__).parent / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m evaluation",
        description="Evaluate RAG retrieval and answer quality.",
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5])
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Also generate answers with the chat model and score them.",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help=(
            "Also grade generated answers with the LLM judge "
            "(JUDGE_PROVIDER / JUDGE_MODEL). Requires --generate."
        ),
    )
    parser.add_argument(
        "--rerank-model",
        default=RERANK_MODEL,
        help="Cross-encoder used by the reranking strategy.",
    )
    parser.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.judge and not args.generate:
        raise SystemExit("--judge grades generated answers; add --generate.")

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    logging.getLogger("evaluation").setLevel(logging.INFO)

    samples = load_dataset(args.dataset)

    components = build_components()
    chunking = components.chunking
    vector_store = components.vector_store

    if vector_store.collection.count() == 0:
        raise SystemExit(
            "The vector store is empty. Upload the documents of the dataset "
            "through POST /upload before running the evaluation."
        )

    strategies = build_strategies(components, rerank_model=args.rerank_model)

    evaluator = Evaluator(
        embedder=components.embedder,
        strategies=strategies,
        ks=args.ks,
        generator=(
            Generator(
                client=build_chat_client(provider=LLM_PROVIDER, model=CHAT_MODEL)
            )
            if args.generate
            else None
        ),
        generation_strategy="hybrid_rrf_rerank",
        generation_top_k=FINAL_TOP_K,
        judge=(
            AnswerJudge(
                client=build_chat_client(provider=JUDGE_PROVIDER, model=JUDGE_MODEL)
            )
            if args.judge
            else None
        ),
    )

    report = evaluator.evaluate(samples)

    documents, _ = vector_store.get_all_chunks()
    report.missing_evidence = metrics.missing_evidence(samples, documents)

    if report.missing_evidence:
        logging.getLogger("evaluation").warning(
            "%d evidence sentences were not found in the index; "
            "see the Missing Evidence section of the report.",
            len(report.missing_evidence),
        )

    metadata = {
        "Date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "Dataset": args.dataset.name,
        "Embedding model": f"{EMBED_PROVIDER}/{EMBED_MODEL}",
        "Chunking": chunking,
        "Reranker": args.rerank_model,
        "Chat model": (
            f"{LLM_PROVIDER}/{CHAT_MODEL}" if args.generate else "not evaluated"
        ),
        "Judge model": (
            f"{JUDGE_PROVIDER}/{JUDGE_MODEL}" if args.judge else "not used"
        ),
        "Candidates per retriever": RETRIEVAL_TOP_K,
    }

    json_path, markdown_path = write_reports(report, args.output, metadata)

    print(markdown_path.read_text(encoding="utf-8"))
    print(f"Reports written to {markdown_path} and {json_path}")


if __name__ == "__main__":
    main()
