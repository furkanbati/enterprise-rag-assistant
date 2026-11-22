
import asyncio
import json
import threading
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
                "title": "",
                "page": 2,
                "chunk": 3,
                "heading": "Introduction",
                "preview": "Python is a programming language.",
            }
        ],
    }


def test_source_preview_skips_the_title_and_heading_lines(monkeypatch):
    chunk = RetrievedChunk(
        document="Python Guide\nIntroduction\n\nPython is a programming language.",
        metadata=ChunkMetadata(
            source="guide.pdf",
            page=2,
            chunk=3,
            heading="Introduction",
            level=1,
            title="Python Guide",
        ),
    )
    monkeypatch.setattr(
        api.pipeline,
        "run",
        lambda question: SimpleNamespace(answer="A language.", chunks=[chunk]),
    )

    source = client.post("/chat", json={"question": "Q?"}).json()["sources"][0]

    assert source["title"] == "Python Guide"
    assert source["preview"] == "Python is a programming language."


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
    assert data["chunking"] == api.chunking_id(
        api.CHUNKING_STRATEGY,
        api.SEMANTIC_PERCENTILE,
        api.SEMANTIC_WINDOW,
        api.CHUNK_CONTEXT,
    )
    assert data["documents"] == [
        {"source": "a.pdf", "chunks": 5},
        {"source": "b.pdf", "chunks": 3},
    ]


def read_sse_events(response):
    """Parse a Server-Sent Events body into (event name, data) pairs."""

    events = []

    for block in response.text.split("\n\n"):
        if not block.strip():
            continue

        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((fields["event"], json.loads(fields["data"])))

    return events


def fake_answer(monkeypatch, tokens=("Python is ", "a language.")):
    monkeypatch.setattr(api.pipeline, "retrieve", lambda question: [make_chunk()])
    monkeypatch.setattr(api.pipeline, "stream", lambda question, chunks: iter(tokens))


def test_chat_stream_sends_server_sent_events_when_asked(monkeypatch):
    fake_answer(monkeypatch, tokens=("Line one\n", "line two."))

    response = client.post(
        "/chat/stream",
        json={"question": "What is Python?"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = read_sse_events(response)
    assert [name for name, _ in events] == ["sources", "token", "token", "done"]
    assert all(name == data["type"] for name, data in events)
    assert events[1][1]["text"] == "Line one\n"
    assert events[0][1]["sources"][0]["source"] == "guide.pdf"


@pytest.mark.parametrize(
    "accept", [None, "*/*", "application/json", "application/x-ndjson"],
)
def test_chat_stream_defaults_to_ndjson(monkeypatch, accept):
    fake_answer(monkeypatch)
    headers = {"Accept": accept} if accept else {}

    response = client.post("/chat/stream", json={"question": "Q?"}, headers=headers)

    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert [event["type"] for event in read_events(response)] == [
        "sources", "token", "token", "done",
    ]


@pytest.mark.parametrize(
    ("accept", "expected"),
    [
        ("text/event-stream", True),
        ("Text/Event-Stream", True),
        ("application/json, text/event-stream;q=0.5", True),
        ("text/event-stream; charset=utf-8", True),
        ("text/event-stream;q=0", False),
        ("text/event-stream;q=bad", False),
        ("*/*", False),
        ("", False),
    ],
)
def test_accepts_event_stream(accept, expected):
    assert api.accepts_event_stream(accept) is expected


@pytest.mark.parametrize("accept", ["application/x-ndjson", "text/event-stream"])
def test_chat_stream_asks_proxies_not_to_buffer(monkeypatch, accept):
    fake_answer(monkeypatch)

    response = client.post(
        "/chat/stream", json={"question": "Q?"}, headers={"Accept": accept},
    )

    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"


def test_chat_stream_reports_time_to_first_token(monkeypatch):
    fake_answer(monkeypatch)

    done = read_events(client.post("/chat/stream", json={"question": "Q?"}))[-1]

    assert done["type"] == "done"
    assert 0 <= done["first_token_ms"] <= done["generation_ms"]


def test_chat_stream_without_tokens_has_no_first_token_time(monkeypatch):
    fake_answer(monkeypatch, tokens=())

    done = read_events(client.post("/chat/stream", json={"question": "Q?"}))[-1]

    assert done["type"] == "done"
    assert done["first_token_ms"] is None


@pytest.mark.parametrize("accept", ["application/x-ndjson", "text/event-stream"])
def test_chat_stream_sends_only_an_error_when_retrieval_fails(monkeypatch, accept):
    def failing_retrieve(question):
        raise RuntimeError("Vector store unavailable")

    monkeypatch.setattr(api.pipeline, "retrieve", failing_retrieve)

    response = client.post(
        "/chat/stream", json={"question": "Q?"}, headers={"Accept": accept},
    )

    if accept == "text/event-stream":
        events = read_sse_events(response)
    else:
        events = [(event["type"], event) for event in read_events(response)]

    assert response.status_code == 200
    assert events == [
        ("error", {"type": "error", "detail": "Vector store unavailable"}),
    ]


def test_stream_events_closes_the_model_stream_when_the_client_leaves(monkeypatch):
    closed = []

    def model_stream(question, chunks):
        try:
            yield "one"
            yield "two"
            yield "three"
        finally:
            closed.append(True)

    monkeypatch.setattr(api.pipeline, "retrieve", lambda question: [])
    monkeypatch.setattr(api.pipeline, "stream", model_stream)

    events = api._stream_events("Q?", api._event)
    assert json.loads(next(events))["type"] == "sources"
    assert json.loads(next(events))["text"] == "one"

    # What the server does when the client disconnects mid-answer.
    events.close()

    assert closed == [True]


def test_close_when_done_closes_the_generator_when_the_response_is_cancelled():
    closed = []
    started = threading.Event()

    def events():
        try:
            yield "sources"
            started.set()
            while True:
                yield "token"
        finally:
            closed.append(True)

    async def consume():
        async for _ in api.close_when_done(events()):
            await asyncio.sleep(0)

    async def run():
        task = asyncio.create_task(consume())

        while not started.is_set():
            await asyncio.sleep(0.01)

        # What Starlette does when the client disconnects.
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(run())

    assert closed == [True]


def test_close_when_done_passes_events_through_and_closes_at_the_end():
    closed = []

    def events():
        try:
            yield "a"
            yield "b"
        finally:
            closed.append(True)

    async def collect():
        return [event async for event in api.close_when_done(events())]

    assert asyncio.run(collect()) == ["a", "b"]
    assert closed == [True]


def test_info_reports_what_turkish_questions_use():
    data = client.get("/info").json()

    assert data["turkish"] == {
        "chat_model": f"{api.LLM_PROVIDER}/{api.CHAT_MODEL_TR}",
        "reranker": api.RERANK_MODEL_TR,
    }


def test_api_routes_turkish_questions_to_their_own_reranker():
    # The defaults: a multilingual reranker for Turkish.
    assert api.RERANK_MODEL_TR != api.RERANK_MODEL
    assert api.retriever.reranker_for("tr").model_name == api.RERANK_MODEL_TR
    assert api.retriever.reranker_for("en") is api.reranker


def test_api_answers_turkish_questions_with_the_turkish_chat_model():
    turkish = api.pipeline.generator_for("tr")

    assert api.pipeline.generator_for("en") is api.generator

    if api.CHAT_MODEL_TR == api.CHAT_MODEL:
        assert turkish is api.generator
    else:
        assert turkish.client.model == api.CHAT_MODEL_TR

        if api.LLM_PROVIDER == "ollama":
            # Thinking stays off for the Turkish model unless set otherwise.
            from providers.ollama import parse_think

            assert turkish.client.think == parse_think(api.OLLAMA_THINK_TR)
