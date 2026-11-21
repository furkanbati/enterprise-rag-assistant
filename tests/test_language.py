import json
from pathlib import Path

import pytest

from language import detect_language

DATASETS = Path(__file__).parent.parent / "evaluation" / "datasets"


def questions(name, language=None):
    rows = [
        json.loads(line)
        for line in (DATASETS / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    return [
        row["question"]
        for row in rows
        if language is None or row.get("language") == language
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("KVKK nedir?", "tr"),
        ("Kurul kaç üyeden oluşur?", "tr"),
        ("VERİ SORUMLUSU KİMDİR?", "tr"),
        ("Veri sorumlusu kimdir", "tr"),
        ("Hangi veriler özel nitelikli sayılır", "tr"),
        ("What is KVKK?", "en"),
        ("What does Müller's theorem state?", "en"),
        ("How does the AI RMF define risk?", "en"),
        ("GOVERN", "en"),
        ("", "en"),
    ],
)
def test_detect_language(text, expected):
    assert detect_language(text) == expected


def test_all_turkish_test_questions_are_detected_as_turkish():
    turkish = questions("ragas_testset.jsonl", "tr")

    assert turkish
    assert [detect_language(q) for q in turkish] == ["tr"] * len(turkish)


@pytest.mark.parametrize(
    "dataset",
    ["ragas_testset.jsonl", "nist_ai_rmf.jsonl", "chunking_benchmark.jsonl"],
)
def test_english_questions_stay_on_the_default_route(dataset):
    english = questions(dataset, "en" if dataset == "ragas_testset.jsonl" else None)

    assert english
    assert [q for q in english if detect_language(q) != "en"] == []
