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
from evaluation.ragas_eval.dataset import RagasSample, load_ragas_dataset
from evaluation.ragas_eval.report import (
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
