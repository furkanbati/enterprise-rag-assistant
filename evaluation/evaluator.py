import logging
import time
from dataclasses import dataclass, field
from statistics import mean

from evaluation import metrics
from evaluation.dataset import EvalSample
from evaluation.strategies import RetrievalStrategy
from generator import Generator
from providers.base import Embedder

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    sample_id: str
    strategy: str
    source: str | None
    retrieved_pages: list[int]
    hit: dict[int, float]
    recall: dict[int, float]
    precision: dict[int, float]
    reciprocal_rank: float
    evidence_recall: dict[int, float | None]
    context_chars: dict[int, int]
    latency_ms: float


@dataclass
class AnswerResult:
    sample_id: str
    question: str
    answer: str
    answerable: bool
    keyword_recall: float | None
    abstained: bool
    latency_ms: float
    citations: list[int]
    # Cited numbers that match none of the chunks given to the model.
    invalid_citations: list[int]


@dataclass
class StrategySummary:
    strategy: str
    hit: dict[int, float]
    recall: dict[int, float]
    precision: dict[int, float]
    mrr: float
    evidence_recall: dict[int, float | None]
    mean_context_chars: dict[int, float]
    mean_latency_ms: float


@dataclass
class GenerationSummary:
    strategy: str
    top_k: int
    answerable_questions: int
    unanswerable_questions: int
    mean_keyword_recall: float | None
    answer_rate: float | None
    abstention_rate: float | None
    mean_latency_ms: float
    # Share of answered, answerable questions with at least one valid citation.
    citation_rate: float | None
    invalid_citation_answers: int


@dataclass
class EvaluationReport:
    ks: list[int]
    num_samples: int
    num_answerable: int
    strategies: list[StrategySummary]
    retrieval_results: list[RetrievalResult]
    generation: GenerationSummary | None = None
    answer_results: list[AnswerResult] = field(default_factory=list)
    missing_evidence: list[tuple[str, str]] = field(default_factory=list)


class Evaluator:
    """Runs a labelled dataset through retrieval strategies and, optionally,
    the answer generator, and aggregates quality metrics."""

    def __init__(
        self,
        embedder: Embedder,
        strategies: dict[str, RetrievalStrategy],
        ks: list[int],
        generator: Generator | None = None,
        generation_strategy: str | None = None,
        generation_top_k: int = 3,
    ) -> None:
        if not strategies:
            raise ValueError("At least one retrieval strategy is required.")

        if not ks or min(ks) < 1:
            raise ValueError("ks must contain positive integers.")

        if generator is not None and generation_strategy not in strategies:
            raise ValueError(
                f"Unknown generation strategy: {generation_strategy}"
            )

        self.embedder = embedder
        self.strategies = strategies
        self.ks = sorted(set(ks))
        self.generator = generator
        self.generation_strategy = generation_strategy
        self.generation_top_k = generation_top_k

    def evaluate(self, samples: list[EvalSample]) -> EvaluationReport:
        retrieval_results: list[RetrievalResult] = []
        answer_results: list[AnswerResult] = []

        max_k = max(self.ks + [self.generation_top_k])

        for index, sample in enumerate(samples, start=1):
            logger.info(
                "Evaluating sample %d/%d: %s",
                index,
                len(samples),
                sample.id,
            )

            embedding = self.embedder.embed(sample.question)

            for name, strategy in self.strategies.items():
                started = time.perf_counter()
                chunks = strategy.retrieve(
                    question=sample.question,
                    embedding=embedding,
                    top_k=max_k,
                )
                latency_ms = (time.perf_counter() - started) * 1000

                if sample.answerable:
                    retrieval_results.append(
                        self._score_retrieval(
                            sample=sample,
                            strategy=name,
                            chunks=chunks,
                            latency_ms=latency_ms,
                        )
                    )

                if (
                    self.generator is not None
                    and name == self.generation_strategy
                ):
                    answer_results.append(
                        self._generate_answer(
                            sample=sample,
                            chunks=chunks[:self.generation_top_k],
                        )
                    )

        answerable = [sample for sample in samples if sample.answerable]

        return EvaluationReport(
            ks=self.ks,
            num_samples=len(samples),
            num_answerable=len(answerable),
            strategies=[
                self._summarize_strategy(name, retrieval_results)
                for name in self.strategies
            ],
            retrieval_results=retrieval_results,
            generation=(
                self._summarize_generation(answer_results)
                if self.generator is not None
                else None
            ),
            answer_results=answer_results,
        )

    def _score_retrieval(
        self,
        sample: EvalSample,
        strategy: str,
        chunks: list,
        latency_ms: float,
    ) -> RetrievalResult:
        return RetrievalResult(
            sample_id=sample.id,
            strategy=strategy,
            source=sample.source,
            retrieved_pages=[chunk.metadata.page for chunk in chunks],
            hit={
                k: metrics.hit_at_k(chunks, sample, k)
                for k in self.ks
            },
            recall={
                k: metrics.recall_at_k(chunks, sample, k)
                for k in self.ks
            },
            precision={
                k: metrics.precision_at_k(chunks, sample, k)
                for k in self.ks
            },
            reciprocal_rank=metrics.reciprocal_rank(
                chunks[:max(self.ks)],
                sample,
            ),
            evidence_recall={
                k: metrics.evidence_recall_at_k(chunks, sample, k)
                for k in self.ks
            },
            context_chars={
                k: metrics.context_chars_at_k(chunks, k)
                for k in self.ks
            },
            latency_ms=latency_ms,
        )

    def _generate_answer(
        self,
        sample: EvalSample,
        chunks: list,
    ) -> AnswerResult:
        started = time.perf_counter()
        answer = self.generator.generate(
            question=sample.question,
            chunks=chunks,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        citations = metrics.cited_sources(answer)

        return AnswerResult(
            sample_id=sample.id,
            question=sample.question,
            answer=answer,
            answerable=sample.answerable,
            keyword_recall=(
                metrics.keyword_recall(answer, sample.expected_keywords)
                if sample.answerable and sample.expected_keywords
                else None
            ),
            abstained=metrics.is_abstention(answer),
            latency_ms=latency_ms,
            citations=citations,
            invalid_citations=[
                number
                for number in citations
                if not 1 <= number <= len(chunks)
            ],
        )

    def _summarize_strategy(
        self,
        strategy: str,
        results: list[RetrievalResult],
    ) -> StrategySummary:
        strategy_results = [
            result
            for result in results
            if result.strategy == strategy
        ]

        return StrategySummary(
            strategy=strategy,
            hit={
                k: _mean(result.hit[k] for result in strategy_results)
                for k in self.ks
            },
            recall={
                k: _mean(result.recall[k] for result in strategy_results)
                for k in self.ks
            },
            precision={
                k: _mean(result.precision[k] for result in strategy_results)
                for k in self.ks
            },
            mrr=_mean(result.reciprocal_rank for result in strategy_results),
            evidence_recall={
                k: _mean_or_none(
                    result.evidence_recall[k] for result in strategy_results
                )
                for k in self.ks
            },
            mean_context_chars={
                k: _mean(result.context_chars[k] for result in strategy_results)
                for k in self.ks
            },
            mean_latency_ms=_mean(
                result.latency_ms for result in strategy_results
            ),
        )

    def _summarize_generation(
        self,
        results: list[AnswerResult],
    ) -> GenerationSummary:
        answerable = [result for result in results if result.answerable]
        unanswerable = [result for result in results if not result.answerable]

        keyword_scores = [
            result.keyword_recall
            for result in answerable
            if result.keyword_recall is not None
        ]

        # Abstentions have nothing to cite, so they do not count against it.
        answered = [result for result in answerable if not result.abstained]

        return GenerationSummary(
            strategy=self.generation_strategy,
            top_k=self.generation_top_k,
            answerable_questions=len(answerable),
            unanswerable_questions=len(unanswerable),
            mean_keyword_recall=(
                mean(keyword_scores) if keyword_scores else None
            ),
            answer_rate=(
                _mean(not result.abstained for result in answerable)
                if answerable
                else None
            ),
            abstention_rate=(
                _mean(result.abstained for result in unanswerable)
                if unanswerable
                else None
            ),
            mean_latency_ms=_mean(result.latency_ms for result in results),
            citation_rate=(
                _mean(
                    len(result.citations) > len(result.invalid_citations)
                    for result in answered
                )
                if answered
                else None
            ),
            invalid_citation_answers=sum(
                bool(result.invalid_citations) for result in results
            ),
        )


def _mean(values) -> float:
    values = [float(value) for value in values]

    return mean(values) if values else 0.0


def _mean_or_none(values) -> float | None:
    """Mean of the values that are not None, or None if there are none."""

    values = [float(value) for value in values if value is not None]

    return mean(values) if values else None
