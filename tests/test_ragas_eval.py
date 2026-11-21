import asyncio
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from evaluation import components as components_module
from evaluation.ragas_eval import __main__ as cli
from evaluation.ragas_eval import metrics as ragas_metrics
from evaluation.ragas_eval import runner as runner_module
from evaluation.ragas_eval.dataset import RagasSample, load_ragas_dataset
from evaluation.ragas_eval.report import (
    load_config_results,
    render_summary,
    write_config_results,
    write_summary,
)
from evaluation.ragas_eval.runner import (
    METRICS,
    RagRecord,
    check_judge,
    collect_records,
    score_records,
    summarize,
)
from models import ChunkMetadata, RetrievedChunk

BUNDLED_DATASET = (
    Path(__file__).parent.parent
    / "evaluation"
    / "datasets"
    / "ragas_testset.jsonl"
)


def make_sample(**overrides):
    values = {
        "id": "q1",
        "question": "What is Python?",
        "reference": "Python is a programming language.",
        "source": "guide.pdf",
        "language": "en",
    }
    values.update(overrides)

    return RagasSample(**values)


def make_chunk(text="Python is a language.", page=1):
    return RetrievedChunk(
        document=text,
        metadata=ChunkMetadata(
            source="guide.pdf",
            page=page,
            chunk=page,
            heading="Intro",
            level=1,
        ),
    )


def make_record(sample_id="q1", language="en", scores=None, **overrides):
    values = {
        "sample_id": sample_id,
        "language": language,
        "question": "What is Python?",
        "reference": "A language.",
        "answer": "A programming language. [1]",
        "contexts": ["Python is a language."],
        "sources": ["guide.pdf p.1"],
        "retrieval_ms": 10.0,
        "generation_ms": 2000.0,
        "scores": dict(scores or {}),
    }
    values.update(overrides)

    return RagRecord(**values)


def write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


class FakeMetric:
    def __init__(self, result=0.5, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def ascore(self, **kwargs):
        self.calls.append(kwargs)

        if self.error:
            raise self.error

        return self.result


# ----------------------------
# Dataset
# ----------------------------

def test_load_ragas_dataset_parses_samples_and_skips_blank_lines(tmp_path):
    path = tmp_path / "set.jsonl"
    path.write_text(
        json.dumps({
            "id": "q1",
            "question": "A?",
            "reference": "A.",
            "source": "a.pdf",
        })
        + "\n\n"
        + json.dumps({
            "id": "t1",
            "question": "B nedir?",
            "reference": "B.",
            "source": "b.pdf",
            "language": "tr",
        }, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    samples = load_ragas_dataset(path)

    assert [sample.id for sample in samples] == ["q1", "t1"]
    assert samples[0].language == "en"
    assert samples[1].question == "B nedir?"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ({"id": "q1", "question": "A?", "reference": " ", "source": "a.pdf"}, "reference"),
        ({"id": "q1", "question": "A?", "reference": "A.", "source": "a.pdf", "language": "de"}, "unknown language"),
        ({"id": "q1", "question": "A?", "source": "a.pdf"}, "line 1"),
    ],
)
def test_load_ragas_dataset_rejects_invalid_samples(tmp_path, row, message):
    path = tmp_path / "set.jsonl"
    write_jsonl(path, [row])

    with pytest.raises(ValueError, match=message):
        load_ragas_dataset(path)


def test_load_ragas_dataset_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "set.jsonl"
    row = {"id": "q1", "question": "A?", "reference": "A.", "source": "a.pdf"}
    write_jsonl(path, [row, row])

    with pytest.raises(ValueError, match="Duplicate"):
        load_ragas_dataset(path)


def test_bundled_ragas_testset_covers_both_languages():
    samples = load_ragas_dataset(BUNDLED_DATASET)

    assert 20 <= len(samples) <= 30
    assert {sample.language for sample in samples} == {"en", "tr"}
    assert {sample.source for sample in samples} == {
        "nist.ai.100-1.pdf",
        "NIST.CSWP.29.pdf",
        "FOMCpresconf20240918.pdf",
        "kvkk_6698.pdf",
    }


# ----------------------------
# Answering
# ----------------------------

def test_collect_records_uses_the_passages_the_generator_saw():
    chunks = [make_chunk("First passage.", page=2), make_chunk("Second.", page=5)]
    strategy = Mock()
    strategy.retrieve.return_value = chunks
    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]
    generator = Mock()
    generator.generate.return_value = "The answer. [1]"
    progress = []

    records = collect_records(
        [make_sample(language="tr")],
        strategy=strategy,
        embedder=embedder,
        generator=generator,
        top_k=2,
        on_progress=lambda done, total: progress.append((done, total)),
    )

    strategy.retrieve.assert_called_once_with(
        question="What is Python?",
        embedding=[0.1, 0.2],
        top_k=2,
    )
    generator.generate.assert_called_once_with(
        question="What is Python?",
        chunks=chunks,
    )
    record = records[0]
    assert record.answer == "The answer. [1]"
    assert record.contexts == ["First passage.", "Second."]
    assert record.sources == ["guide.pdf p.2", "guide.pdf p.5"]
    assert record.language == "tr"
    assert record.reference == "Python is a programming language."
    assert progress == [(1, 1)]


def test_collect_records_keeps_going_when_generation_fails():
    strategy = Mock()
    strategy.retrieve.return_value = [make_chunk()]
    generator = Mock()
    generator.generate.side_effect = [RuntimeError("model offline"), "Answer."]

    records = collect_records(
        [make_sample(id="q1"), make_sample(id="q2")],
        strategy=strategy,
        embedder=Mock(),
        generator=generator,
        top_k=3,
    )

    assert records[0].answer == ""
    assert records[0].errors == {"generation": "model offline"}
    assert records[1].answer == "Answer."


# ----------------------------
# Scoring
# ----------------------------

def test_score_records_passes_each_metric_only_its_inputs():
    metrics = {name: FakeMetric(0.8) for name in METRICS}
    record = make_record()

    asyncio.run(score_records([record], metrics))

    assert metrics["faithfulness"].calls == [{
        "user_input": "What is Python?",
        "response": "A programming language. [1]",
        "retrieved_contexts": ["Python is a language."],
    }]
    assert set(metrics["answer_relevancy"].calls[0]) == {"user_input", "response"}
    assert set(metrics["context_precision"].calls[0]) == {
        "user_input", "reference", "retrieved_contexts",
    }
    assert set(metrics["context_recall"].calls[0]) == {
        "user_input", "retrieved_contexts", "reference",
    }
    assert record.scores == {name: 0.8 for name in METRICS}
    assert record.errors == {}


def test_score_records_unwraps_results_and_records_failures():
    metrics = {
        "faithfulness": FakeMetric(SimpleNamespace(value=0.25)),
        "answer_relevancy": FakeMetric(float("nan")),
        "context_precision": FakeMetric(error=ValueError("bad JSON")),
        "context_recall": FakeMetric(1),
    }
    record = make_record()

    asyncio.run(score_records([record], metrics))

    assert record.scores == {
        "faithfulness": 0.25,
        "answer_relevancy": None,
        "context_precision": None,
        "context_recall": 1.0,
    }
    assert record.errors["answer_relevancy"] == "the judge returned no score"
    assert record.errors["context_precision"] == "ValueError: bad JSON"


def test_score_records_skips_answer_metrics_without_an_answer():
    metrics = {name: FakeMetric(0.5) for name in METRICS}
    record = make_record(answer="  ")

    asyncio.run(score_records([record], metrics))

    assert record.scores["faithfulness"] is None
    assert record.scores["answer_relevancy"] is None
    assert record.scores["context_recall"] == 0.5
    assert metrics["faithfulness"].calls == []
    assert record.errors["faithfulness"] == "no answer generated"


def test_score_records_skips_all_metrics_without_passages():
    metrics = {name: FakeMetric(0.5) for name in METRICS}
    record = make_record(contexts=[])

    asyncio.run(score_records([record], metrics))

    assert record.scores == {name: None for name in METRICS}
    assert all(metric.calls == [] for metric in metrics.values())


def test_score_records_limits_concurrent_requests():
    running = 0
    peak = 0

    class SlowMetric:
        async def ascore(self, **kwargs):
            nonlocal running, peak
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1
            return 1.0

    records = [make_record(sample_id=f"q{i}") for i in range(6)]

    asyncio.run(score_records(records, {"faithfulness": SlowMetric()}, concurrency=2))

    assert peak == 2


def test_summarize_averages_scored_questions_overall_and_by_language():
    records = [
        make_record("q1", "en", {name: 1.0 for name in METRICS}),
        make_record(
            "q2",
            "en",
            {**{name: 0.5 for name in METRICS}, "faithfulness": None},
            retrieval_ms=30.0,
        ),
        make_record("t1", "tr", {name: 0.0 for name in METRICS}),
    ]

    summary = summarize("hybrid", records)

    assert summary.strategy == "hybrid_rrf"
    assert summary.questions == 3
    assert summary.scores["faithfulness"] == pytest.approx(0.5)
    assert summary.scores["context_recall"] == pytest.approx(0.5)
    assert summary.scores_by_language["en"]["faithfulness"] == pytest.approx(1.0)
    assert summary.scores_by_language["tr"]["context_recall"] == pytest.approx(0.0)
    assert summary.unscored["faithfulness"] == 1
    assert summary.mean_retrieval_ms == pytest.approx(50 / 3)


# ----------------------------
# Reports
# ----------------------------

def write_result(tmp_path, config, score, language_scores=None):
    records = [make_record("q1", "en", {name: score for name in METRICS})]

    if language_scores is not None:
        records.append(
            make_record("t1", "tr", {name: language_scores for name in METRICS})
        )

    return write_config_results(
        tmp_path,
        summarize(config, records),
        records,
        {"Judge model": "openai/judge", "Date": f"date-{config}"},
    )


def test_write_config_results_writes_json_and_csv(tmp_path):
    json_path, csv_path = write_result(tmp_path, "vector", 0.75)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["summary"]["config"] == "vector"
    assert data["records"][0]["answer"] == "A programming language. [1]"

    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["id"] == "q1"
    assert rows[0]["faithfulness"] == "0.7500"
    assert rows[0]["sources"] == "guide.pdf p.1"


def test_write_summary_combines_configurations_in_a_fixed_order(tmp_path):
    write_result(tmp_path, "hybrid_rerank", 0.9, language_scores=0.4)
    write_result(tmp_path, "vector", 0.6, language_scores=0.2)

    text = write_summary(tmp_path).read_text(encoding="utf-8")

    assert text.index("`vector`") < text.index("`hybrid_rerank`")
    assert "| `hybrid_rerank` | Vector + BM25, RRF, cross-encoder reranking | **0.650** |" in text
    assert "| `vector` | Vector search only | 0.400 |" in text
    assert "### By language" in text
    assert "| `vector` | Turkish | 0.200 |" in text
    # Shared settings appear once, differing ones per configuration.
    assert "- **Judge model:** openai/judge" in text
    assert "`vector` date-vector" in text


def test_render_summary_does_not_bold_a_single_configuration(tmp_path):
    write_result(tmp_path, "vector", 0.6)

    text = write_summary(tmp_path).read_text(encoding="utf-8")

    assert "**0.600**" not in text
    assert "0.600" in text
    assert "### By language" not in text


ANSWER_METRICS = ("faithfulness", "answer_relevancy")


def write_partial_result(tmp_path, config, score, metric_names=ANSWER_METRICS):
    records = [make_record("q1", "en", {name: score for name in metric_names})]

    return write_config_results(
        tmp_path,
        summarize(config, records, metric_names=metric_names),
        records,
        {"Judge model": "openai/judge"},
    )


def test_reports_show_only_the_computed_metrics(tmp_path):
    _, csv_path = write_partial_result(tmp_path, "vector", 0.5)
    write_partial_result(tmp_path, "hybrid", 0.7)

    with open(csv_path, encoding="utf-8", newline="") as f:
        header = next(csv.reader(f))

    text = write_summary(tmp_path).read_text(encoding="utf-8")

    assert "faithfulness" in header and "context_recall" not in header
    assert "| Configuration | Retrieval | Faithfulness | Answer relevancy |" in text
    assert "Context recall" not in text
    assert "| `hybrid` | Vector + BM25, Reciprocal Rank Fusion | **0.700** | **0.700** |" in text


def test_summary_marks_metrics_a_configuration_did_not_compute(tmp_path):
    write_result(tmp_path, "vector", 0.6)
    write_partial_result(tmp_path, "hybrid", 0.7)

    text = write_summary(tmp_path).read_text(encoding="utf-8")

    assert "| `hybrid` | Vector + BM25, Reciprocal Rank Fusion | **0.700** | **0.700** | — | — |" in text
    # The only value of a column is its best.
    assert "| `vector` | Vector search only | 0.600 | 0.600 | **0.600** | **0.600** |" in text


def test_render_summary_without_results():
    assert "No results yet" in render_summary([])


# ----------------------------
# Command line
# ----------------------------

def test_parse_args_defaults_to_the_production_configuration():
    args = cli.parse_args([])

    assert args.config == "hybrid_rerank"
    assert args.dataset.name == "ragas_testset.jsonl"
    assert args.output.parts[-2:] == ("results", "ragas")


def test_parse_args_computes_all_metrics_unless_told_otherwise():
    assert cli.parse_args([]).metrics == list(METRICS)
    assert cli.parse_args(
        ["--metrics", "faithfulness", "answer_relevancy"]
    ).metrics == ["faithfulness", "answer_relevancy"]

    with pytest.raises(SystemExit):
        cli.parse_args(["--metrics", "bleu"])


def test_select_metrics_keeps_the_standard_order_without_duplicates():
    metrics = {name: object() for name in METRICS}

    selected = cli.select_metrics(
        metrics,
        ["answer_relevancy", "faithfulness", "answer_relevancy"],
    )

    assert list(selected) == ["faithfulness", "answer_relevancy"]
    assert selected["faithfulness"] is metrics["faithfulness"]


def test_parse_args_rejects_unknown_configuration():
    with pytest.raises(SystemExit):
        cli.parse_args(["--config", "bm25_only"])


def test_select_samples_filters_language_then_limits():
    samples = [
        make_sample(id="q1"),
        make_sample(id="t1", language="tr"),
        make_sample(id="t2", language="tr"),
    ]

    assert [s.id for s in cli.select_samples(samples, "tr", 1)] == ["t1"]
    assert [s.id for s in cli.select_samples(samples, None, None)] == ["q1", "t1", "t2"]


def test_resolve_judge_model(monkeypatch):
    monkeypatch.setattr(cli, "JUDGE_PROVIDER", "openai")
    monkeypatch.setattr(cli, "JUDGE_MODEL", "my-judge")

    assert cli.resolve_judge_model("openai", None) == "my-judge"
    assert cli.resolve_judge_model("ollama", None) == "llama3"
    assert cli.resolve_judge_model("ollama", "qwen3") == "qwen3"


def make_components(indexed):
    vector_store = Mock()
    vector_store.list_sources.return_value = {name: 10 for name in indexed}

    return SimpleNamespace(vector_store=vector_store)


def test_ensure_documents_indexed_stops_when_documents_are_missing(tmp_path):
    with pytest.raises(SystemExit, match="guide.pdf"):
        cli.ensure_documents_indexed(
            [make_sample()],
            make_components([]),
            ingest=False,
            documents_dir=tmp_path,
        )


def test_ensure_documents_indexed_ingests_missing_documents(tmp_path, monkeypatch):
    (tmp_path / "guide.pdf").write_bytes(b"%PDF")
    ingestion = Mock()
    ingestion.ingest.return_value = SimpleNamespace(chunks=4)
    monkeypatch.setattr(cli, "build_ingestion", lambda components: ingestion)

    cli.ensure_documents_indexed(
        [make_sample(), make_sample(id="q2", source="other.pdf")],
        make_components(["other.pdf"]),
        ingest=True,
        documents_dir=tmp_path,
    )

    ingestion.ingest.assert_called_once_with(str(tmp_path / "guide.pdf"))


def test_ensure_documents_indexed_reports_files_it_cannot_find(tmp_path):
    with pytest.raises(SystemExit, match="not found"):
        cli.ensure_documents_indexed(
            [make_sample()],
            make_components([]),
            ingest=True,
            documents_dir=tmp_path,
        )


# ----------------------------
# Components and judge clients
# ----------------------------

def test_build_strategies_builds_only_the_requested_ones(monkeypatch):
    reranker = Mock(side_effect=AssertionError("reranker should not load"))
    monkeypatch.setattr(components_module, "CrossEncoderReranker", reranker)
    components = SimpleNamespace(
        vector_search=Mock(),
        keyword_search=Mock(),
        fusion=Mock(),
    )

    strategies = components_module.build_strategies(
        components,
        rerank_model="model",
        names=["vector", "hybrid_rrf"],
    )

    assert list(strategies) == ["vector", "hybrid_rrf"]


def test_build_strategies_rejects_unknown_names():
    with pytest.raises(ValueError, match="Unknown retrieval strategy"):
        components_module.build_strategies(Mock(), "model", names=["magic"])


def test_ollama_judge_uses_the_openai_compatible_endpoint(monkeypatch):
    monkeypatch.setattr(ragas_metrics, "OLLAMA_HOST", "http://ollama:11434/")

    client = ragas_metrics._async_client("ollama")

    assert str(client.base_url).rstrip("/") == "http://ollama:11434/v1"


def test_openai_judge_requires_a_key(monkeypatch):
    monkeypatch.setattr(ragas_metrics, "OPENAI_API_KEY", "")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        ragas_metrics._async_client("openai")


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gpt-6.1-sol", True),
        ("gpt-6-luna", True),
        ("gpt-5", True),
        ("o3-mini", True),
        ("gpt-4o", False),
        ("gpt-4.1-mini", False),
        ("llama3", False),
    ],
)
def test_is_reasoning_model(model, expected):
    assert ragas_metrics.is_reasoning_model(model) is expected


def test_reasoning_model_args_replace_unsupported_parameters(monkeypatch):
    monkeypatch.setattr(ragas_metrics, "OPENAI_REASONING_EFFORT", "low")

    args = ragas_metrics.reasoning_model_args(
        {"temperature": 0.01, "top_p": 0.1, "max_tokens": 4096}
    )

    assert args == {
        "temperature": 1.0,
        "max_completion_tokens": 4096,
        "reasoning_effort": "low",
    }


def test_check_judge_passes_when_the_judge_answers():
    metric = FakeMetric(1.0)

    asyncio.run(check_judge({"context_recall": metric}))

    assert set(metric.calls[0]) == {"user_input", "retrieved_contexts", "reference"}


def test_check_judge_fails_when_the_judge_rejects_requests():
    metrics = {"faithfulness": FakeMetric(error=ValueError("max_tokens unsupported"))}

    with pytest.raises(RuntimeError, match="max_tokens unsupported"):
        asyncio.run(check_judge(metrics))


def test_unknown_judge_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown RAGAS provider"):
        ragas_metrics._async_client("acme")


def test_build_ragas_metrics_builds_the_four_metrics(monkeypatch):
    pytest.importorskip("ragas")
    monkeypatch.setattr(ragas_metrics, "OLLAMA_HOST", "http://ollama:11434")

    metrics = ragas_metrics.build_ragas_metrics(
        judge_provider="ollama",
        judge_model="llama3",
        embed_provider="ollama",
        embed_model="nomic-embed-text",
    )

    assert list(metrics) == list(METRICS)


def test_build_ragas_metrics_adapts_parameters_for_reasoning_judges(monkeypatch):
    pytest.importorskip("ragas")
    monkeypatch.setattr(ragas_metrics, "OPENAI_API_KEY", "sk-test")

    metrics = ragas_metrics.build_ragas_metrics(
        judge_provider="openai",
        judge_model="gpt-6.1-sol",
        embed_provider="ollama",
        embed_model="nomic-embed-text",
    )

    model_args = metrics["faithfulness"].llm.model_args
    assert "max_tokens" not in model_args
    assert model_args["max_completion_tokens"] == ragas_metrics.JUDGE_MAX_TOKENS


# ----------------------------
# Lost connection to the judge
# ----------------------------

class ConnectError(Exception):
    """Named like httpx.ConnectError, which the runner recognises by name."""


class FlakyMetric:
    """Fails with a network error the first `failures` times, then scores."""

    def __init__(self, failures, result=0.9, error=None):
        self.failures = failures
        self.result = result
        self.error = error or ConnectError("connection refused")
        self.calls = 0

    async def ascore(self, **kwargs):
        self.calls += 1

        if self.calls <= self.failures:
            raise self.error

        return self.result


def no_sleep(delays):
    async def sleep(seconds):
        delays.append(seconds)

    return sleep


def test_is_network_error_follows_the_cause_chain():
    try:
        try:
            raise ConnectError("dns failure")
        except ConnectError as e:
            raise RuntimeError("APIConnectionError: Connection error.") from e
    except RuntimeError as wrapped:
        assert runner_module.is_network_error(wrapped)

    assert runner_module.is_network_error(TimeoutError())
    assert not runner_module.is_network_error(ValueError("bad JSON"))


def test_score_records_retries_while_the_judge_is_unreachable():
    delays = []
    metric = FlakyMetric(failures=3)
    record = make_record()

    asyncio.run(score_records(
        [record],
        {"faithfulness": metric},
        retry_wait=600,
        sleep=no_sleep(delays),
    ))

    assert record.scores == {"faithfulness": 0.9}
    assert record.errors == {}
    assert delays == list(runner_module.RETRY_DELAYS[:3])


def test_score_records_gives_up_after_the_wait_and_keeps_the_error():
    delays = []
    metric = FlakyMetric(failures=100)
    record = make_record()

    asyncio.run(score_records(
        [record],
        {"faithfulness": metric},
        retry_wait=50,
        sleep=no_sleep(delays),
    ))

    assert record.scores == {"faithfulness": None}
    assert record.errors["faithfulness"].startswith("ConnectError")
    assert sum(delays) == 50


def test_score_records_does_not_retry_errors_other_than_network_ones():
    delays = []
    metric = FlakyMetric(failures=1, error=ValueError("bad JSON"))
    record = make_record()

    asyncio.run(score_records(
        [record],
        {"faithfulness": metric},
        retry_wait=600,
        sleep=no_sleep(delays),
    ))

    assert metric.calls == 1
    assert delays == []
    assert record.errors["faithfulness"] == "ValueError: bad JSON"


def test_score_records_only_missing_keeps_existing_scores():
    metric = FakeMetric(0.7)
    scored = make_record(sample_id="q1", scores={"faithfulness": 0.4})
    unscored = make_record(sample_id="q2", scores={"faithfulness": None})
    unscored.errors["faithfulness"] = "ConnectError: connection refused"

    asyncio.run(score_records(
        [scored, unscored],
        {"faithfulness": metric},
        only_missing=True,
    ))

    assert len(metric.calls) == 1
    assert scored.scores["faithfulness"] == 0.4
    assert unscored.scores["faithfulness"] == 0.7
    assert unscored.errors == {}


def test_check_judge_waits_for_the_judge_to_come_back():
    delays = []
    metric = FlakyMetric(failures=2)

    asyncio.run(check_judge(
        {"faithfulness": metric},
        retry_wait=600,
        sleep=no_sleep(delays),
    ))

    assert metric.calls == 3


def test_check_judge_without_wait_fails_on_the_first_network_error():
    with pytest.raises(RuntimeError, match="connection refused"):
        asyncio.run(check_judge({"faithfulness": FlakyMetric(failures=1)}))


def test_load_config_results_restores_records_and_metrics(tmp_path):
    record = make_record(scores={"faithfulness": 0.5, "answer_relevancy": None})
    summary = summarize(
        "vector", [record], metric_names=("faithfulness", "answer_relevancy")
    )
    write_config_results(tmp_path, summary, [record], {"Chat model": "x"})

    metadata, metric_names, records = load_config_results(tmp_path, "vector")

    assert metadata == {"Chat model": "x"}
    assert metric_names == ["faithfulness", "answer_relevancy"]
    assert records == [record]
    assert load_config_results(tmp_path, "hybrid") is None


def test_rescore_fills_missing_scores_without_answering_again(tmp_path, monkeypatch):
    records = [
        make_record(sample_id="q1", scores={"faithfulness": 0.5, "answer_relevancy": 0.6}),
        make_record(sample_id="q2", scores={"faithfulness": None, "answer_relevancy": 0.8}),
    ]
    records[1].errors["faithfulness"] = "ConnectError: connection refused"
    names = ("faithfulness", "answer_relevancy")
    write_config_results(
        tmp_path,
        summarize("vector", records, metric_names=names),
        records,
        {"Chat model": "ollama/llama3"},
    )

    metrics = {name: FakeMetric(0.9) for name in METRICS}
    monkeypatch.setattr(ragas_metrics, "build_ragas_metrics", lambda **kwargs: metrics)
    monkeypatch.setattr(
        cli, "build_components", Mock(side_effect=AssertionError("no answering"))
    )

    cli.main(["--config", "all", "--rescore", "--output", str(tmp_path)])

    _, metric_names, rescored = load_config_results(tmp_path, "vector")
    assert metric_names == list(names)
    assert [r.scores["faithfulness"] for r in rescored] == [0.5, 0.9]
    assert rescored[1].errors == {}
    # The judge test request plus the one missing score; the metrics the run
    # did not compute are not requested.
    assert len(metrics["faithfulness"].calls) == 2
    assert len(metrics["answer_relevancy"].calls) == 0
    assert metrics["context_recall"].calls == []
    assert metrics["context_precision"].calls == []
    assert "| `vector` |" in (tmp_path / "summary.md").read_text(encoding="utf-8")


def test_run_saves_answers_before_scoring(tmp_path, monkeypatch):
    record = make_record(scores={})

    class Interrupted(Exception):
        pass

    async def interrupted(*args, **kwargs):
        raise Interrupted

    monkeypatch.setattr(cli, "build_components", lambda: SimpleNamespace(
        chunking="sentence-ctx", embedder=None,
    ))
    monkeypatch.setattr(cli, "ensure_documents_indexed", lambda *a, **k: None)
    monkeypatch.setattr(cli, "build_strategies", lambda *a, **k: {"vector": None})
    monkeypatch.setattr(cli, "build_chat_client", lambda **k: None)
    monkeypatch.setattr(cli, "Generator", lambda **k: None)
    monkeypatch.setattr(cli, "check_judge", lambda *a, **k: asyncio.sleep(0))
    monkeypatch.setattr(cli, "collect_records", lambda *a, **k: [record])
    monkeypatch.setattr(cli, "score_records", interrupted)
    monkeypatch.setattr(
        ragas_metrics,
        "build_ragas_metrics",
        lambda **kwargs: {name: FakeMetric() for name in METRICS},
    )

    with pytest.raises(Interrupted):
        cli.main([
            "--config", "vector",
            "--metrics", "faithfulness",
            "--limit", "1",
            "--output", str(tmp_path),
        ])

    _, metric_names, saved = load_config_results(tmp_path, "vector")
    assert metric_names == ["faithfulness"]
    assert saved[0].answer == record.answer
    assert saved[0].contexts == record.contexts


def test_score_records_waits_without_limit_by_default_in_the_cli():
    assert cli.parse_args([]).judge_wait is None
    assert cli.judge_wait_seconds(cli.parse_args(["--judge-wait", "2"])) == 120

    delays = []
    metric = FlakyMetric(failures=8)
    record = make_record()

    asyncio.run(score_records(
        [record],
        {"faithfulness": metric},
        retry_wait=None,
        sleep=no_sleep(delays),
    ))

    assert record.scores == {"faithfulness": 0.9}
    assert len(delays) == 8
    assert max(delays) == runner_module.RETRY_DELAYS[-1]


def test_judge_worker_runs_jobs_in_order_and_reports_failures():
    worker = runner_module.JudgeWorker()
    order = []

    async def job(name, delay):
        await asyncio.sleep(delay)
        order.append(name)

    async def failing():
        raise ValueError("judge broke")

    try:
        worker.submit(job("first", 0.05))
        worker.submit(job("second", 0))
        assert worker.run(job("direct", 0)) is None
        worker.submit(failing())

        with pytest.raises(ValueError, match="judge broke"):
            worker.wait()
    finally:
        worker.close()

    assert order.index("first") < order.index("second")


def patch_run_dependencies(monkeypatch, collect_records):
    monkeypatch.setattr(cli, "build_components", lambda: SimpleNamespace(
        chunking="sentence-ctx", embedder=None,
    ))
    monkeypatch.setattr(cli, "ensure_documents_indexed", lambda *a, **k: None)
    monkeypatch.setattr(
        cli,
        "build_strategies",
        lambda *a, **k: {name: name for name in cli.CONFIGS.values()},
    )
    monkeypatch.setattr(cli, "build_chat_client", lambda **k: None)
    monkeypatch.setattr(cli, "Generator", lambda **k: None)
    monkeypatch.setattr(cli, "collect_records", collect_records)
    monkeypatch.setattr(
        ragas_metrics,
        "build_ragas_metrics",
        lambda **kwargs: {name: FakeMetric() for name in METRICS},
    )


def test_answering_goes_on_while_the_judge_waits_for_the_connection(
    tmp_path, monkeypatch,
):
    answered = []
    scored = []

    def collect(samples, strategy, **kwargs):
        answered.append(strategy)
        return [make_record(scores={})]

    async def unreachable(*args, **kwargs):
        try:
            raise ConnectError("network is unreachable")
        except ConnectError as e:
            raise RuntimeError(f"The judge model failed a test request: {e}") from e

    async def score_when_back(records, metrics, **kwargs):
        # The "connection" comes back only after every configuration has
        # been answered: if scoring blocked answering, this would never end.
        for _ in range(500):
            if len(answered) == len(cli.CONFIGS):
                break
            await asyncio.sleep(0.01)
        else:
            raise AssertionError("answering waited for the judge")

        assert kwargs["retry_wait"] is None
        for record in records:
            record.scores = {name: 0.5 for name in metrics}
        scored.append(len(answered))

    patch_run_dependencies(monkeypatch, collect)
    monkeypatch.setattr(cli, "check_judge", unreachable)
    monkeypatch.setattr(cli, "score_records", score_when_back)

    cli.main([
        "--config", "all",
        "--metrics", "faithfulness",
        "--limit", "1",
        "--output", str(tmp_path),
    ])

    assert answered == list(cli.CONFIGS.values())
    assert scored == [3, 3, 3]
    for config in cli.CONFIGS:
        _, _, records = load_config_results(tmp_path, config)
        assert records[0].scores == {"faithfulness": 0.5}
    assert (tmp_path / "summary.md").exists()


def test_run_stops_when_the_judge_rejects_the_test_request(tmp_path, monkeypatch):
    collect = Mock()

    async def rejected(*args, **kwargs):
        raise RuntimeError("The judge model failed a test request: invalid API key")

    patch_run_dependencies(monkeypatch, collect)
    monkeypatch.setattr(cli, "check_judge", rejected)

    with pytest.raises(SystemExit, match="invalid API key"):
        cli.main(["--config", "vector", "--limit", "1", "--output", str(tmp_path)])

    collect.assert_not_called()


def test_run_loads_the_reranker_before_answering(tmp_path, monkeypatch):
    events = []
    reranker = SimpleNamespace(
        model=None,
        model_name="cross-encoder/test",
        load=lambda: events.append("reranker loaded"),
    )

    def collect(samples, strategy, **kwargs):
        events.append(f"answered {strategy}")
        return [make_record(scores={})]

    patch_run_dependencies(monkeypatch, collect)
    monkeypatch.setattr(
        cli,
        "build_strategies",
        lambda *a, **k: {
            "vector": "vector",
            "hybrid_rrf_rerank": SimpleNamespace(reranker=reranker),
        },
    )
    monkeypatch.setattr(cli, "check_judge", lambda *a, **k: asyncio.sleep(0))

    cli.main([
        "--config", "vector",
        "--metrics", "faithfulness",
        "--limit", "1",
        "--output", str(tmp_path),
    ])

    assert events == ["reranker loaded", "answered vector"]


def test_build_strategies_adds_the_turkish_reranker_only_when_it_differs(monkeypatch):
    built = []
    monkeypatch.setattr(
        components_module,
        "CrossEncoderReranker",
        lambda name: built.append(name) or SimpleNamespace(model_name=name, model=None),
    )
    components = SimpleNamespace(vector_search=Mock(), keyword_search=Mock(), fusion=Mock())

    routed = components_module.build_strategies(
        components, rerank_model="en-model", names=["hybrid_rrf_rerank"],
        rerank_model_tr="tr-model",
    )["hybrid_rrf_rerank"]
    same = components_module.build_strategies(
        components, rerank_model="en-model", names=["hybrid_rrf_rerank"],
        rerank_model_tr="en-model",
    )["hybrid_rrf_rerank"]

    assert routed.language_rerankers["tr"].model_name == "tr-model"
    assert same.language_rerankers == {}
    assert built == ["en-model", "tr-model", "en-model"]


def test_load_local_models_loads_the_turkish_reranker_too():
    loaded = []

    def reranker(name):
        return SimpleNamespace(model=None, model_name=name, load=lambda: loaded.append(name))

    strategy = SimpleNamespace(
        rerankers=lambda: [reranker("en-model"), reranker("tr-model")],
    )

    cli.load_local_models({"hybrid_rrf_rerank": strategy})

    assert loaded == ["en-model", "tr-model"]


def test_collect_records_answers_turkish_questions_with_the_turkish_generator():
    strategy = Mock()
    strategy.retrieve.return_value = [make_chunk()]
    embedder = Mock()
    embedder.embed.return_value = [0.1]
    default, turkish = Mock(), Mock()
    default.generate.return_value = "default"
    turkish.generate.return_value = "turkish"

    records = collect_records(
        [
            make_sample(id="q1", question="What is Python?"),
            make_sample(id="t1", question="Veri sorumlusu kimdir?", language="tr"),
        ],
        strategy=strategy,
        embedder=embedder,
        generator=default,
        top_k=3,
        language_generators={"tr": turkish},
    )

    assert [record.answer for record in records] == ["default", "turkish"]
