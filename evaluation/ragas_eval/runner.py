"""Answer the test questions with one retrieval configuration and score the
answers with RAGAS metrics."""

import asyncio
import concurrent.futures
import logging
import math
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Protocol

from evaluation.ragas_eval.dataset import RagasSample
from evaluation.strategies import RetrievalStrategy
from generator import Generator
from providers.base import Embedder

logger = logging.getLogger(__name__)

# Configuration name on the command line -> retrieval strategy it runs.
CONFIGS = {
    "vector": "vector",
    "hybrid": "hybrid_rrf",
    "hybrid_rerank": "hybrid_rrf_rerank",
}

CONFIG_DESCRIPTIONS = {
    "vector": "Vector search only",
    "hybrid": "Vector + BM25, Reciprocal Rank Fusion",
    "hybrid_rerank": "Vector + BM25, RRF, cross-encoder reranking",
}

METRICS = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)

# The inputs each RAGAS metric's ascore() takes.
METRIC_INPUTS = {
    "faithfulness": ("user_input", "response", "retrieved_contexts"),
    "answer_relevancy": ("user_input", "response"),
    "context_precision": ("user_input", "reference", "retrieved_contexts"),
    "context_recall": ("user_input", "retrieved_contexts", "reference"),
}

# Metrics that grade the answer cannot score an empty one.
NEEDS_RESPONSE = {"faithfulness", "answer_relevancy"}

# Exceptions (by class name, anywhere in the cause chain) that mean the judge
# could not be reached, as opposed to a judge that answered badly. Names, not
# classes, so the runner does not import openai or httpx.
NETWORK_ERRORS = {
    "APIConnectionError",
    "APITimeoutError",
    "ConnectError",
    "ConnectTimeout",
    "ReadTimeout",
    "WriteTimeout",
    "PoolTimeout",
    "NetworkError",
    "RemoteProtocolError",
    "ConnectionError",
    "TimeoutError",
    "gaierror",
}

# Seconds between attempts while the judge is unreachable.
RETRY_DELAYS = (15, 30, 60, 120, 300)

Sleep = Callable[[float], Awaitable[None]]


class Metric(Protocol):
    async def ascore(self, **kwargs: Any) -> Any: ...


@dataclass
class RagRecord:
    """One question answered with one configuration, and its scores."""

    sample_id: str
    language: str
    question: str
    reference: str
    answer: str
    contexts: list[str]
    sources: list[str]
    retrieval_ms: float
    generation_ms: float
    scores: dict[str, float | None] = field(default_factory=dict)
    # Metric name, or "generation", -> why it has no value.
    errors: dict[str, str] = field(default_factory=dict)


@dataclass
class ConfigSummary:
    config: str
    strategy: str
    questions: int
    # Metric -> mean over the questions it could score.
    scores: dict[str, float | None]
    # Language -> metric -> mean.
    scores_by_language: dict[str, dict[str, float | None]]
    # Metric -> questions it could not score.
    unscored: dict[str, int]
    mean_retrieval_ms: float
    mean_generation_ms: float


def collect_records(
    samples: list[RagasSample],
    strategy: RetrievalStrategy,
    embedder: Embedder,
    generator: Generator,
    top_k: int,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[RagRecord]:
    """Retrieve and answer every question; the passages the generator saw
    become the RAGAS contexts."""

    records: list[RagRecord] = []

    for index, sample in enumerate(samples, start=1):
        started = time.perf_counter()
        chunks = strategy.retrieve(
            question=sample.question,
            embedding=embedder.embed(sample.question),
            top_k=top_k,
        )
        retrieval_ms = (time.perf_counter() - started) * 1000

        record = RagRecord(
            sample_id=sample.id,
            language=sample.language,
            question=sample.question,
            reference=sample.reference,
            answer="",
            contexts=[chunk.document for chunk in chunks],
            sources=[
                f"{chunk.metadata.source} p.{chunk.metadata.page}"
                for chunk in chunks
            ],
            retrieval_ms=retrieval_ms,
            generation_ms=0.0,
        )

        started = time.perf_counter()

        try:
            record.answer = generator.generate(
                question=sample.question,
                chunks=chunks,
            )
        except Exception as e:
            logger.warning("Generation failed for %s: %s", sample.id, e)
            record.errors["generation"] = str(e)

        record.generation_ms = (time.perf_counter() - started) * 1000
        records.append(record)

        if on_progress:
            on_progress(index, len(samples))

    return records


def is_network_error(error: BaseException) -> bool:
    """Whether the error, or one it was raised from, means the judge could not
    be reached (no connection, DNS failure, timeout)."""

    seen: set[int] = set()
    current: BaseException | None = error

    while current is not None and id(current) not in seen:
        seen.add(id(current))

        if any(cls.__name__ in NETWORK_ERRORS for cls in type(current).__mro__):
            return True

        current = current.__cause__ or current.__context__

    return False


class JudgeWorker:
    """Runs the judge calls on an event loop in a background thread, so that
    answering, which needs only the local model, goes on while the judge
    scores, or waits for the connection to come back.

    Everything goes through one loop because the async clients keep their
    connections, which belong to the loop that opened them, and fail with
    "Event loop is closed" in another loop. Submitted jobs run one at a time,
    in order."""

    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self.loop.run_forever,
            name="judge",
            daemon=True,
        )
        self._thread.start()
        self._futures: list[concurrent.futures.Future] = []
        self._lock = self.run(_new_lock())

    def run(self, coro: Awaitable[Any]) -> Any:
        """Run a coroutine on the judge loop and wait for its result."""

        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def submit(self, coro: Awaitable[Any]) -> concurrent.futures.Future:
        """Queue a coroutine after the ones already submitted, without
        waiting for it."""

        async def in_turn() -> Any:
            async with self._lock:
                return await coro

        future = asyncio.run_coroutine_threadsafe(in_turn(), self.loop)
        self._futures.append(future)

        return future

    def pending(self) -> int:
        return sum(not future.done() for future in self._futures)

    def wait(self) -> None:
        """Wait for every submitted job; re-raises the first that failed."""

        for future in self._futures:
            future.result()

    def close(self) -> None:
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._thread.join()
        self.loop.close()


async def _new_lock() -> asyncio.Lock:
    return asyncio.Lock()


async def call_judge(
    call: Callable[[], Awaitable[Any]],
    retry_wait: float | None = 0,
    sleep: Sleep = asyncio.sleep,
    label: str = "judge",
) -> Any:
    """Run one judge request. While the judge cannot be reached, wait and try
    again for up to retry_wait seconds in total, or for as long as it takes
    when retry_wait is None; any other error, and a network error after that
    time, is raised."""

    waited = 0.0
    attempt = 0

    while True:
        try:
            return await call()
        except Exception as e:
            if not is_network_error(e):
                raise

            if retry_wait is not None and waited >= retry_wait:
                raise

            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]

            if retry_wait is not None:
                delay = min(delay, retry_wait - waited)

            logger.warning(
                "%s: judge unreachable (%s), retrying in %.0f s",
                label,
                type(e).__name__,
                delay,
            )
            await sleep(delay)
            waited += delay
            attempt += 1


async def score_records(
    records: list[RagRecord],
    metrics: dict[str, Metric],
    concurrency: int = 1,
    retry_wait: float | None = 0,
    only_missing: bool = False,
    sleep: Sleep = asyncio.sleep,
) -> None:
    """Score every record with every metric, storing the results on the
    records. A metric that fails on a record leaves that score empty and
    records why, so one bad judge reply does not stop the run.

    While the judge cannot be reached, a request is retried for up to
    retry_wait seconds. With only_missing, scores a record already has are
    kept and not requested again."""

    semaphore = asyncio.Semaphore(max(concurrency, 1))

    async def score(record: RagRecord, name: str, metric: Metric) -> None:
        if only_missing and record.scores.get(name) is not None:
            return

        record.errors.pop(name, None)

        inputs = {
            "user_input": record.question,
            "response": record.answer,
            "retrieved_contexts": record.contexts,
            "reference": record.reference,
        }

        if not record.contexts:
            record.scores[name] = None
            record.errors[name] = "no passages retrieved"
            return

        if name in NEEDS_RESPONSE and not record.answer.strip():
            record.scores[name] = None
            record.errors[name] = "no answer generated"
            return

        async with semaphore:
            try:
                result = await call_judge(
                    lambda: metric.ascore(
                        **{key: inputs[key] for key in METRIC_INPUTS[name]}
                    ),
                    retry_wait=retry_wait,
                    sleep=sleep,
                    label=f"{name} {record.sample_id}",
                )
            except Exception as e:
                logger.warning("%s failed for %s: %s", name, record.sample_id, e)
                record.scores[name] = None
                record.errors[name] = f"{type(e).__name__}: {e}"
                return

        value = _as_float(result)
        record.scores[name] = value

        if value is None:
            record.errors[name] = "the judge returned no score"

    await asyncio.gather(*(
        score(record, name, metric)
        for record in records
        for name, metric in metrics.items()
    ))


async def check_judge(
    metrics: dict[str, Metric],
    retry_wait: float | None = 0,
    sleep: Sleep = asyncio.sleep,
) -> None:
    """Score one trivial example, so that a judge that cannot be reached or
    rejects the request fails the run before any answers are generated,
    instead of every score failing at the end. With retry_wait, an
    unreachable judge is waited for up to that many seconds."""

    name = "context_recall" if "context_recall" in metrics else next(iter(metrics))
    metric = metrics[name]
    inputs = {
        "user_input": "What colour is the sky on a clear day?",
        "response": "The sky is blue on a clear day.",
        "retrieved_contexts": ["On a clear day the sky is blue."],
        "reference": "The sky is blue on a clear day.",
    }

    try:
        await call_judge(
            lambda: metric.ascore(**{key: inputs[key] for key in METRIC_INPUTS[name]}),
            retry_wait=retry_wait,
            sleep=sleep,
            label="test request",
        )
    except Exception as e:
        raise RuntimeError(f"The judge model failed a test request: {e}") from e


def summarize(
    config: str,
    records: list[RagRecord],
    metric_names: tuple[str, ...] = METRICS,
) -> ConfigSummary:
    languages = sorted({record.language for record in records})

    return ConfigSummary(
        config=config,
        strategy=CONFIGS.get(config, config),
        questions=len(records),
        scores=_means(records, metric_names),
        scores_by_language={
            language: _means(
                [record for record in records if record.language == language],
                metric_names,
            )
            for language in languages
        },
        unscored={
            name: sum(record.scores.get(name) is None for record in records)
            for name in metric_names
        },
        mean_retrieval_ms=_mean([record.retrieval_ms for record in records]),
        mean_generation_ms=_mean([record.generation_ms for record in records]),
    )


def _means(
    records: list[RagRecord],
    metric_names: tuple[str, ...],
) -> dict[str, float | None]:
    means: dict[str, float | None] = {}

    for name in metric_names:
        values = [
            record.scores[name]
            for record in records
            if record.scores.get(name) is not None
        ]
        means[name] = mean(values) if values else None

    return means


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _as_float(result: Any) -> float | None:
    """A metric result as a float; RAGAS returns a MetricResult wrapping the
    value, and NaN when it could not decide."""

    value = getattr(result, "value", result)

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    return None if math.isnan(value) else value
