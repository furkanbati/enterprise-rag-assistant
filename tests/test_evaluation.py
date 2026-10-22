import json
from unittest.mock import Mock

import pytest

from evaluation import metrics
from evaluation.dataset import EvalSample, load_dataset
from evaluation.evaluator import Evaluator
from evaluation.report import render_markdown, write_reports
from evaluation.strategies import HybridRerankStrategy, HybridStrategy
from models import ChunkMetadata, RetrievedChunk
from retrieval.fusion import ReciprocalRankFusion


def make_chunk(page, chunk=None, source="guide.pdf", document="text"):
    return RetrievedChunk(
        document=document,
        metadata=ChunkMetadata(
            source=source,
            page=page,
            chunk=page if chunk is None else chunk,
            heading="Heading",
            level=1,
        ),
    )


def make_sample(**overrides):
    values = {
        "id": "q1",
        "question": "What is Python?",
        "relevant_pages": [2, 4],
        "expected_keywords": ["programming", "language"],
    }
    values.update(overrides)

    return EvalSample(**values)


# ----------------------------
# Dataset
# ----------------------------

def test_load_dataset_parses_samples_and_skips_blank_lines(tmp_path):
    path = tmp_path / "dataset.jsonl"
    path.write_text(
        json.dumps({"id": "q1", "question": "A?", "relevant_pages": [1]})
        + "\n\n"
        + json.dumps({"id": "q2", "question": "B?", "answerable": False})
        + "\n",
        encoding="utf-8",
    )

    samples = load_dataset(path)

    assert [sample.id for sample in samples] == ["q1", "q2"]
    assert samples[0].relevant_pages == [1]
    assert samples[1].answerable is False


def test_load_dataset_rejects_answerable_sample_without_labels(tmp_path):
    path = tmp_path / "dataset.jsonl"
    path.write_text(
        json.dumps({"id": "q1", "question": "A?"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no relevant_pages"):
        load_dataset(path)


def test_load_dataset_reports_invalid_line(tmp_path):
    path = tmp_path / "dataset.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="line 1"):
        load_dataset(path)


def test_bundled_dataset_is_valid():
    samples = load_dataset("evaluation/datasets/nist_ai_rmf.jsonl")

    assert len(samples) >= 20
    assert len({sample.id for sample in samples}) == len(samples)
    assert any(not sample.answerable for sample in samples)


def test_load_dataset_reads_evidence(tmp_path):
    path = tmp_path / "dataset.jsonl"
    path.write_text(
        json.dumps({
            "id": "q1",
            "question": "A?",
            "relevant_pages": [1],
            "evidence": ["Python is a language."],
        }) + "\n",
        encoding="utf-8",
    )

    assert load_dataset(path)[0].evidence == ["Python is a language."]


def test_chunking_benchmark_dataset_is_valid():
    samples = load_dataset("evaluation/datasets/chunking_benchmark.jsonl")
    answerable = [sample for sample in samples if sample.answerable]

    assert len({sample.id for sample in samples}) == len(samples)
    assert len({sample.source for sample in answerable}) == 3
    assert all(sample.source and sample.evidence for sample in answerable)
    assert any(not sample.answerable for sample in samples)


# ----------------------------
# Metrics
# ----------------------------

def test_retrieval_metrics_use_page_level_relevance():
    sample = make_sample()
    chunks = [make_chunk(1), make_chunk(2), make_chunk(2, chunk=9), make_chunk(4)]

    assert metrics.hit_at_k(chunks, sample, 1) == 0.0
    assert metrics.hit_at_k(chunks, sample, 2) == 1.0
    assert metrics.recall_at_k(chunks, sample, 3) == 0.5
    assert metrics.recall_at_k(chunks, sample, 4) == 1.0
    assert metrics.precision_at_k(chunks, sample, 4) == 0.75
    assert metrics.reciprocal_rank(chunks, sample) == 0.5


def test_retrieval_metrics_handle_no_relevant_chunks():
    sample = make_sample()
    chunks = [make_chunk(7), make_chunk(8)]

    assert metrics.hit_at_k(chunks, sample, 2) == 0.0
    assert metrics.recall_at_k(chunks, sample, 2) == 0.0
    assert metrics.reciprocal_rank(chunks, sample) == 0.0
    assert metrics.precision_at_k([], sample, 3) == 0.0


def test_relevance_respects_source_when_specified():
    sample = make_sample(source="other.pdf")

    assert not metrics.is_relevant(make_chunk(2), sample)
    assert metrics.is_relevant(make_chunk(2, source="other.pdf"), sample)


def test_evidence_recall_counts_sentences_found_in_top_k():
    sample = make_sample(
        evidence=["Python is a language.", "It was created by Guido."],
    )
    chunks = [
        make_chunk(1, document="Intro. PYTHON is a\nlanguage."),
        make_chunk(2, document="It was created by Guido. More text."),
    ]

    assert metrics.evidence_recall_at_k(chunks, sample, 1) == 0.5
    assert metrics.evidence_recall_at_k(chunks, sample, 2) == 1.0
    assert metrics.evidence_recall_at_k([], sample, 2) == 0.0


def test_evidence_recall_ignores_chunks_from_other_sources():
    sample = make_sample(source="guide.pdf", evidence=["Python is a language."])
    chunks = [make_chunk(1, source="other.pdf", document="Python is a language.")]

    assert metrics.evidence_recall_at_k(chunks, sample, 1) == 0.0


def test_evidence_recall_is_none_without_evidence():
    assert metrics.evidence_recall_at_k([make_chunk(1)], make_sample(), 1) is None


def test_context_chars_sums_top_k_chunks():
    chunks = [make_chunk(1, document="abc"), make_chunk(2, document="defgh")]

    assert metrics.context_chars_at_k(chunks, 1) == 3
    assert metrics.context_chars_at_k(chunks, 5) == 8


def test_missing_evidence_lists_sentences_not_in_index():
    samples = [
        make_sample(evidence=["Python is a language.", "Not indexed."]),
        make_sample(id="q2"),
    ]

    missing = metrics.missing_evidence(
        samples,
        ["Heading\n\nPython is a  language. More."],
    )

    assert missing == [("q1", "Not indexed.")]


def test_keyword_recall_is_case_and_hyphen_insensitive():
    answer = "Bias can be systemic, computational and Human cognitive."

    assert metrics.keyword_recall(
        answer,
        ["systemic", "human-cognitive", "statistical"],
    ) == pytest.approx(2 / 3)
    assert metrics.keyword_recall(answer, []) == 0.0


@pytest.mark.parametrize(
    "answer",
    [
        "I don't know.",
        "I don’t know based on the context.",
        "The context does not mention any funding amount.",
        "This information is not provided in the context.",
    ],
)
def test_is_abstention_detects_refusals(answer):
    assert metrics.is_abstention(answer)


def test_is_abstention_ignores_regular_answers():
    assert not metrics.is_abstention(
        "The four functions are GOVERN, MAP, MEASURE, and MANAGE."
    )


# ----------------------------
# Strategies
# ----------------------------

def test_hybrid_strategy_fuses_candidates_and_truncates():
    vector_search = Mock()
    vector_search.search.return_value = [make_chunk(1), make_chunk(2)]
    keyword_search = Mock()
    keyword_search.search.return_value = [make_chunk(2), make_chunk(3)]

    strategy = HybridStrategy(
        vector_search=vector_search,
        keyword_search=keyword_search,
        fusion=ReciprocalRankFusion(),
        candidate_top_k=10,
    )

    results = strategy.retrieve("question", [0.1], top_k=2)

    assert [chunk.metadata.page for chunk in results] == [2, 1]
    vector_search.search.assert_called_once_with(embedding=[0.1], top_k=10)
    keyword_search.search.assert_called_once_with(query="question", top_k=10)


def test_hybrid_rerank_strategy_reranks_fused_candidates():
    vector_search = Mock()
    vector_search.search.return_value = [make_chunk(1)]
    keyword_search = Mock()
    keyword_search.search.return_value = [make_chunk(3)]
    reranker = Mock()
    reranked = [make_chunk(3)]
    reranker.rerank.return_value = reranked

    strategy = HybridRerankStrategy(
        vector_search=vector_search,
        keyword_search=keyword_search,
        fusion=ReciprocalRankFusion(),
        reranker=reranker,
        candidate_top_k=5,
    )

    assert strategy.retrieve("question", [0.1], top_k=1) == reranked

    kwargs = reranker.rerank.call_args.kwargs
    assert kwargs["question"] == "question"
    assert kwargs["top_k"] == 1
    assert {chunk.metadata.page for chunk in kwargs["chunks"]} == {1, 3}


# ----------------------------
# Evaluator
# ----------------------------

def make_evaluator(generator=None):
    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]

    good = Mock()
    good.retrieve.return_value = [make_chunk(2), make_chunk(4), make_chunk(5)]

    bad = Mock()
    bad.retrieve.return_value = [make_chunk(7), make_chunk(8), make_chunk(2)]

    evaluator = Evaluator(
        embedder=embedder,
        strategies={"good": good, "bad": bad},
        ks=[1, 3],
        generator=generator,
        generation_strategy="good",
        generation_top_k=2,
    )

    return evaluator, embedder, good


def test_evaluator_aggregates_metrics_per_strategy():
    evaluator, embedder, good = make_evaluator()
    samples = [
        make_sample(),
        make_sample(id="q2", relevant_pages=[], answerable=False),
    ]

    report = evaluator.evaluate(samples)

    assert report.num_samples == 2
    assert report.num_answerable == 1
    assert report.generation is None

    summaries = {summary.strategy: summary for summary in report.strategies}
    assert summaries["good"].hit == {1: 1.0, 3: 1.0}
    assert summaries["good"].recall == {1: 0.5, 3: 1.0}
    assert summaries["good"].mrr == 1.0
    assert summaries["bad"].hit == {1: 0.0, 3: 1.0}
    assert summaries["bad"].mrr == pytest.approx(1 / 3)

    # Unanswerable questions are excluded from retrieval metrics.
    assert {result.sample_id for result in report.retrieval_results} == {"q1"}

    # Each question is embedded once and shared by all strategies.
    assert embedder.embed.call_count == 2
    good.retrieve.assert_called_with(
        question="What is Python?",
        embedding=[0.1, 0.2],
        top_k=3,
    )


def test_evaluator_scores_generated_answers():
    generator = Mock()
    generator.generate.side_effect = [
        "Python is a programming language.",
        "I don't know.",
    ]
    evaluator, _, _ = make_evaluator(generator=generator)
    samples = [
        make_sample(),
        make_sample(id="q2", relevant_pages=[], answerable=False),
    ]

    report = evaluator.evaluate(samples)

    assert generator.generate.call_count == 2
    first_call = generator.generate.call_args_list[0].kwargs
    assert [chunk.metadata.page for chunk in first_call["chunks"]] == [2, 4]

    assert report.generation.mean_keyword_recall == 1.0
    assert report.generation.answer_rate == 1.0
    assert report.generation.abstention_rate == 1.0
    assert [result.abstained for result in report.answer_results] == [
        False,
        True,
    ]


def test_evaluator_rejects_unknown_generation_strategy():
    with pytest.raises(ValueError, match="Unknown generation strategy"):
        Evaluator(
            embedder=Mock(),
            strategies={"vector": Mock()},
            ks=[1],
            generator=Mock(),
            generation_strategy="missing",
        )


# ----------------------------
# Report
# ----------------------------

def test_reports_are_written_as_json_and_markdown(tmp_path):
    generator = Mock()
    generator.generate.return_value = "Python is a programming language."
    evaluator, _, _ = make_evaluator(generator=generator)
    report = evaluator.evaluate([make_sample()])

    json_path, markdown_path = write_reports(
        report,
        tmp_path / "results",
        metadata={"Dataset": "test.jsonl"},
    )

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["metadata"] == {"Dataset": "test.jsonl"}
    assert data["num_samples"] == 1

    markdown = markdown_path.read_text(encoding="utf-8")
    assert markdown == render_markdown(report, {"Dataset": "test.jsonl"})
    assert "| `good` | 1.000 | 1.000 | 0.500 | 1.000 | 1.000 |" in markdown
    assert "## Answer Generation" in markdown
    assert "> Python is a programming language." in markdown


def make_evidence_evaluator():
    embedder = Mock()
    embedder.embed.return_value = [0.1, 0.2]

    strategy = Mock()
    strategy.retrieve.return_value = [
        make_chunk(2, document="Python is a language."),
        make_chunk(4, document="Unrelated text."),
    ]

    return Evaluator(
        embedder=embedder,
        strategies={"good": strategy},
        ks=[1, 2],
    )


def test_evaluator_averages_evidence_over_labelled_samples_only():
    report = make_evidence_evaluator().evaluate([
        make_sample(source="guide.pdf", evidence=["Python is a language."]),
        make_sample(id="q2", source="guide.pdf"),
    ])

    summary = report.strategies[0]
    assert summary.evidence_recall == {1: 1.0, 2: 1.0}
    assert summary.mean_context_chars == {1: 21.0, 2: 36.0}

    results = {result.sample_id: result for result in report.retrieval_results}
    assert results["q2"].evidence_recall == {1: None, 2: None}
    assert results["q1"].source == "guide.pdf"


def test_report_has_no_evidence_sections_without_evidence_labels():
    evaluator, _, _ = make_evaluator()
    report = evaluator.evaluate([make_sample()])

    assert "Evidence" not in render_markdown(report, {})


def test_report_shows_evidence_by_source_and_missing_evidence():
    report = make_evidence_evaluator().evaluate([
        make_sample(source="guide.pdf", evidence=["Python is a language."]),
    ])
    report.missing_evidence = [("q9", "Not\nindexed.")]

    markdown = render_markdown(report, {})

    assert "## Evidence Coverage" in markdown
    assert "| `good` | 1.000 | 1.000 | 21 | 36 |" in markdown
    assert "### Evidence@2 by Source" in markdown
    assert "| Strategy | guide.pdf |" in markdown
    assert "## Missing Evidence" in markdown
    assert "- `q9`: Not indexed." in markdown
