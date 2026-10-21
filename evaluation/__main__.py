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
    CHROMA_PATH,
    COLLECTION_NAME,
    EMBED_MODEL,
    FINAL_TOP_K,
    OLLAMA_HOST,
    RERANK_MODEL,
    RETRIEVAL_TOP_K,
)
from evaluation.dataset import load_dataset
from evaluation.evaluator import Evaluator
from evaluation.report import write_reports
from evaluation.strategies import (
    HybridRerankStrategy,
    HybridStrategy,
    KeywordOnlyStrategy,
    VectorOnlyStrategy,
)
from generator import Generator
from providers.ollama import OllamaChatClient, OllamaEmbedder
from retrieval.fusion import ReciprocalRankFusion
from retrieval.keyword_search import KeywordSearch
from retrieval.reranker import CrossEncoderReranker
from retrieval.vector_search import VectorSearch
from vector_store import VectorStore

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
        "--rerank-model",
        default=RERANK_MODEL,
        help="Cross-encoder used by the reranking strategy.",
    )
    parser.add_argument("--verbose", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    logging.getLogger("evaluation").setLevel(logging.INFO)

    samples = load_dataset(args.dataset)

    vector_store = VectorStore(
        path=CHROMA_PATH,
        collection_name=COLLECTION_NAME,
    )

    if vector_store.collection.count() == 0:
        raise SystemExit(
            "The vector store is empty. Upload the evaluation document "
            "through POST /upload before running the evaluation."
        )

    embedder = OllamaEmbedder(model=EMBED_MODEL, host=OLLAMA_HOST)
    vector_search = VectorSearch(vector_store)
    keyword_search = KeywordSearch(vector_store)
    keyword_search.rebuild()
    fusion = ReciprocalRankFusion()

    strategies = {
        "vector": VectorOnlyStrategy(vector_search),
        "bm25": KeywordOnlyStrategy(keyword_search),
        "hybrid_rrf": HybridStrategy(
            vector_search=vector_search,
            keyword_search=keyword_search,
            fusion=fusion,
            candidate_top_k=RETRIEVAL_TOP_K,
        ),
        "hybrid_rrf_rerank": HybridRerankStrategy(
            vector_search=vector_search,
            keyword_search=keyword_search,
            fusion=fusion,
            reranker=CrossEncoderReranker(args.rerank_model),
            candidate_top_k=RETRIEVAL_TOP_K,
        ),
    }

    evaluator = Evaluator(
        embedder=embedder,
        strategies=strategies,
        ks=args.ks,
        generator=(
            Generator(
                client=OllamaChatClient(model=CHAT_MODEL, host=OLLAMA_HOST)
            )
            if args.generate
            else None
        ),
        generation_strategy="hybrid_rrf_rerank",
        generation_top_k=FINAL_TOP_K,
    )

    report = evaluator.evaluate(samples)

    metadata = {
        "Date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "Dataset": args.dataset.name,
        "Embedding model": EMBED_MODEL,
        "Reranker": args.rerank_model,
        "Chat model": CHAT_MODEL if args.generate else "not evaluated",
        "Candidates per retriever": RETRIEVAL_TOP_K,
    }

    json_path, markdown_path = write_reports(report, args.output, metadata)

    print(markdown_path.read_text(encoding="utf-8"))
    print(f"Reports written to {markdown_path} and {json_path}")


if __name__ == "__main__":
    main()
