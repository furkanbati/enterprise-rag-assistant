
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import api
from models import ChunkMetadata, IngestionResult, RetrievedChunk


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


def test_upload_indexes_document_from_a_temporary_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    ingested = []

    def fake_ingest(file_path):
        ingested.append((Path(file_path), Path(file_path).read_bytes()))
        return IngestionResult(source="guide.pdf", chunks=4, replaced=False)

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
        "message": "Document indexed successfully.",
        "source": "guide.pdf",
        "chunks": 4,
        "replaced": False,
    }

    [(path, content)] = ingested
    assert path.name == "guide.pdf"
    assert content == b"Fake PDF content"
    # The upload is not kept in the working directory or the temporary one.
    assert not (tmp_path / "guide.pdf").exists()
    assert not path.exists()


def fake_ingest_recording(ingested):
    def ingest(file_path):
        ingested.append(file_path)
        return IngestionResult(source=Path(file_path).name, chunks=1, replaced=False)

    return ingest


def test_upload_keeps_only_the_file_name(monkeypatch):
    ingested = []
    monkeypatch.setattr(api.ingestion, "ingest", fake_ingest_recording(ingested))

    response = client.post(
        "/upload",
        files={"file": ("../../etc/guide.pdf", b"PDF", "application/pdf")},
    )

    assert response.status_code == 200
    assert Path(ingested[0]).name == "guide.pdf"
    assert ".." not in Path(ingested[0]).parts


def test_upload_rejects_unsupported_file_types(monkeypatch):
    ingested = []
    monkeypatch.setattr(api.ingestion, "ingest", fake_ingest_recording(ingested))

    response = client.post(
        "/upload",
        files={"file": ("setup.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert ".docx" in response.json()["detail"]
    assert ingested == []


@pytest.mark.parametrize(
    "name",
    ["guide.PDF", "policy.docx", "page.html", "page.htm", "notes.md", "notes.txt"],
)
def test_upload_accepts_every_supported_format(monkeypatch, name):
    ingested = []
    monkeypatch.setattr(api.ingestion, "ingest", fake_ingest_recording(ingested))

    response = client.post("/upload", files={"file": (name, b"content")})

    assert response.status_code == 200
    assert Path(ingested[0]).name == name


def test_upload_reports_a_replaced_document(monkeypatch):
    monkeypatch.setattr(
        api.ingestion,
        "ingest",
        lambda file_path: IngestionResult(source="guide.pdf", chunks=9, replaced=True),
    )

    response = client.post("/upload", files={"file": ("guide.pdf", b"PDF")})

    assert response.json()["replaced"] is True
    assert response.json()["chunks"] == 9


def test_upload_returns_422_for_a_document_without_text(monkeypatch):
    def no_text(file_path):
        raise ValueError("No text could be extracted from scan.pdf.")

    monkeypatch.setattr(api.ingestion, "ingest", no_text)

    response = client.post("/upload", files={"file": ("scan.pdf", b"PDF")})

    assert response.status_code == 422
    assert response.json()["detail"] == "No text could be extracted from scan.pdf."


def test_documents_lists_indexed_documents(monkeypatch):
    monkeypatch.setattr(api.vector_store, "list_sources", lambda: {"b.md": 2, "a.pdf": 5})

    response = client.get("/documents")

    assert response.json() == [
        {"source": "a.pdf", "chunks": 5},
        {"source": "b.md", "chunks": 2},
    ]


def test_delete_document_removes_chunks_and_rebuilds_keyword_index(monkeypatch):
    deleted = []
    rebuilt = []
    monkeypatch.setattr(
        api.vector_store,
        "delete_source",
        lambda source: deleted.append(source) or 3,
    )
    monkeypatch.setattr(api.keyword_search, "rebuild", lambda: rebuilt.append(True))

    response = client.delete("/documents/My%20Policy.pdf")

    assert response.status_code == 200
    assert response.json() == {"source": "My Policy.pdf", "deleted_chunks": 3}
    assert deleted == ["My Policy.pdf"]
    assert rebuilt == [True]


def test_delete_unknown_document_returns_404(monkeypatch):
    monkeypatch.setattr(api.vector_store, "delete_source", lambda source: 0)
    monkeypatch.setattr(
        api.keyword_search,
        "rebuild",
        lambda: pytest.fail("rebuild should not be called"),
    )

    response = client.delete("/documents/missing.pdf")

    assert response.status_code == 404


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


def read_events(response):
    return [json.loads(line) for line in response.text.splitlines() if line]


def test_chat_stream_sends_sources_then_tokens_then_done(monkeypatch):
    chunk = make_chunk(
        document="Introduction\n\nPython is a programming language.",
        source="guide.pdf",
        page=2,
    )
    calls = []

    monkeypatch.setattr(api.pipeline, "retrieve", lambda question: [chunk])

    def fake_stream(question, chunks):
        calls.append((question, chunks))
        yield "Python is "
        yield "a language."

    monkeypatch.setattr(api.pipeline, "stream", fake_stream)

    response = client.post("/chat/stream", json={"question": "What is Python?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")

    events = read_events(response)
    assert [event["type"] for event in events] == ["sources", "token", "token", "done"]
    assert events[0]["sources"][0]["source"] == "guide.pdf"
    assert events[0]["sources"][0]["preview"] == "Python is a programming language."
    assert "".join(event["text"] for event in events[1:3]) == "Python is a language."
    assert {"retrieval_ms", "generation_ms"} <= events[3].keys()
    assert calls == [("What is Python?", [chunk])]


def test_chat_stream_ends_with_error_event_when_generation_fails(monkeypatch):
    monkeypatch.setattr(api.pipeline, "retrieve", lambda question: [])

    def failing_stream(question, chunks):
        yield "Partial"
        raise RuntimeError("Model unavailable")

    monkeypatch.setattr(api.pipeline, "stream", failing_stream)

    response = client.post("/chat/stream", json={"question": "Q?"})

    events = read_events(response)
    assert [event["type"] for event in events] == ["sources", "token", "error"]
    assert events[-1]["detail"] == "Model unavailable"


def test_info_reports_models_and_indexed_documents(monkeypatch):
    monkeypatch.setattr(
        api.vector_store,
        "list_sources",
        lambda: {"b.pdf": 3, "a.pdf": 5},
    )

    response = client.get("/info")

    assert response.status_code == 200
    data = response.json()
    assert data["chat_model"] == f"{api.LLM_PROVIDER}/{api.CHAT_MODEL}"
    assert data["embedding_model"] == f"{api.EMBED_PROVIDER}/{api.EMBED_MODEL}"
    assert data["chunking"] == api.CHUNKING_STRATEGY
    assert data["documents"] == [
        {"source": "a.pdf", "chunks": 5},
        {"source": "b.pdf", "chunks": 3},
    ]
