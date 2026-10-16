
from types import SimpleNamespace

from fastapi.testclient import TestClient

import api
from models import ChunkMetadata, RetrievedChunk


client = TestClient(api.app)


def make_chunk(
    document="Python is a programming language.",
    heading="Introduction",
    source="guide.pdf",
    page=1,
    chunk=0,
):
    return RetrievedChunk(
        document=document,
        metadata=ChunkMetadata(
            source=source,
            page=page,
            chunk=chunk,
            heading=heading,
            level=1,
        ),
    )


def test_upload_indexes_document_successfully(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    ingested_paths = []

    def fake_ingest(file_path):
        ingested_paths.append(file_path)

    monkeypatch.setattr(api.ingestion, "ingest", fake_ingest)

    response = client.post(
        "/upload",
        files={
            "file": (
                "guide.pdf",
                b"Fake PDF content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Document indexed successfully."
    }
    assert ingested_paths == ["guide.pdf"]
    assert (tmp_path / "guide.pdf").read_bytes() == b"Fake PDF content"


def test_upload_returns_500_when_ingestion_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def fake_ingest(file_path):
        raise RuntimeError("Indexing failed")

    monkeypatch.setattr(api.ingestion, "ingest", fake_ingest)

    response = client.post(
        "/upload",
        files={
            "file": (
                "guide.pdf",
                b"Fake PDF content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 500
    assert "Failed to index document" in response.json()["detail"]
    assert "Indexing failed" in response.json()["detail"]


def test_chat_returns_answer_and_source_metadata(monkeypatch):
    chunk = make_chunk(
        document="Introduction\n\nPython is a programming language.",
        heading="Introduction",
        source="guide.pdf",
        page=2,
        chunk=3,
    )

    monkeypatch.setattr(
        api.pipeline,
        "run",
        lambda question: SimpleNamespace(
            answer="Python is a programming language.",
            chunks=[chunk],
        ),
    )

    response = client.post(
        "/chat",
        json={"question": "What is Python?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Python is a programming language.",
        "sources": [
            {
                "source": "guide.pdf",
                "page": 2,
                "chunk": 3,
                "heading": "Introduction",
                "preview": "Python is a programming language.",
            }
        ],
    }


def test_chat_truncates_source_preview_to_200_characters(monkeypatch):
    document = "A" * 250
    chunk = make_chunk(
        document=document,
        heading="",
    )

    monkeypatch.setattr(
        api.pipeline,
        "run",
        lambda question: SimpleNamespace(
            answer="Answer",
            chunks=[chunk],
        ),
    )

    response = client.post(
        "/chat",
        json={"question": "Summarize the document"},
    )

    assert response.status_code == 200
    assert len(response.json()["sources"][0]["preview"]) == 200


def test_chat_returns_empty_sources_when_no_chunks_found(monkeypatch):
    monkeypatch.setattr(
        api.pipeline,
        "run",
        lambda question: SimpleNamespace(
            answer="I don't know.",
            chunks=[],
        ),
    )

    response = client.post(
        "/chat",
        json={"question": "Unknown question"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "I don't know.",
        "sources": [],
    }


def test_chat_returns_500_when_pipeline_fails(monkeypatch):
    def fake_run(question):
        raise RuntimeError("Generation failed")

    monkeypatch.setattr(api.pipeline, "run", fake_run)

    response = client.post(
        "/chat",
        json={"question": "What is Python?"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Generation failed"


def test_chat_returns_422_when_question_is_missing():
    response = client.post("/chat", json={})

    assert response.status_code == 422
