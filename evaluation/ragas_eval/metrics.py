"""Build the RAGAS metrics with a configurable judge.

Both providers are reached through the OpenAI client: Ollama serves an
OpenAI-compatible API under /v1, so a local judge needs no extra packages.
"""

import os

from config import (
    OLLAMA_HOST,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_REASONING_EFFORT,
)
from providers.factory import PROVIDERS

# RAGAS sends usage analytics unless this is set; keep evaluations private.
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")

# Statement extraction and verdicts for long answers need room, and
# reasoning models spend part of the budget on reasoning.
JUDGE_MAX_TOKENS = 4096

# A local judge on a CPU can take minutes for one structured reply.
OPENAI_TIMEOUT_SECONDS = 120.0
OLLAMA_TIMEOUT_SECONDS = 900.0


def build_ragas_metrics(
    judge_provider: str,
    judge_model: str,
    embed_provider: str,
    embed_model: str,
) -> dict:
    """The four RAGAS metrics, keyed like ``runner.METRICS``."""

    from ragas.embeddings import OpenAIEmbeddings
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    llm = llm_factory(
        judge_model,
        provider="openai",
        client=_async_client(judge_provider),
        max_tokens=JUDGE_MAX_TOKENS,
    )

    if judge_provider == "openai" and is_reasoning_model(judge_model):
        llm.model_args = reasoning_model_args(llm.model_args)

    embeddings = OpenAIEmbeddings(
        client=_async_client(embed_provider),
        model=embed_model,
    )

    return {
        "faithfulness": Faithfulness(llm=llm),
        "answer_relevancy": AnswerRelevancy(llm=llm, embeddings=embeddings),
        "context_precision": ContextPrecision(llm=llm),
        "context_recall": ContextRecall(llm=llm),
    }


def is_reasoning_model(model: str) -> bool:
    """Whether an OpenAI model is a reasoning model (o-series, GPT-5 and
    later), which rejects max_tokens and sampling parameters.

    RAGAS detects these itself, but not with a dotted version such as
    gpt-6.1, so the judge would send parameters the API rejects.
    """

    name = model.lower()

    if len(name) >= 2 and name[0] == "o" and name[1].isdigit():
        return True

    if name.startswith("gpt-"):
        version = name[4:].split("-")[0]

        try:
            return float(version) >= 5
        except ValueError:
            return False

    return False


def reasoning_model_args(model_args: dict) -> dict:
    """The judge's request parameters adapted to a reasoning model."""

    args = dict(model_args)
    max_tokens = args.pop("max_tokens", JUDGE_MAX_TOKENS)
    args.setdefault("max_completion_tokens", max_tokens)
    # Reasoning models only accept the default temperature and no top_p.
    args["temperature"] = 1.0
    args.pop("top_p", None)

    if OPENAI_REASONING_EFFORT:
        args.setdefault("reasoning_effort", OPENAI_REASONING_EFFORT)

    return args


def _async_client(provider: str):
    from openai import AsyncOpenAI

    if provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY must be set to use 'openai' as the RAGAS "
                "judge or embedding provider."
            )

        return AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            timeout=OPENAI_TIMEOUT_SECONDS,
        )

    if provider == "ollama":
        return AsyncOpenAI(
            # Ollama ignores the key, but the client requires one.
            api_key="ollama",
            base_url=f"{OLLAMA_HOST.rstrip('/')}/v1",
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )

    choices = " or ".join(f"'{name}'" for name in PROVIDERS)
    raise ValueError(f"Unknown RAGAS provider '{provider}'. Use {choices}.")
