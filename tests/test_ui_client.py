
import json

import pytest
import requests

from ui import client as client_module
from ui.client import ApiClient, ApiError, parse_events


class FakeResponse:
    def __init__(self, status_code=200, body=None, lines=None, reason="OK"):
        self.status_code = status_code
        self.ok = status_code < 400
        self.reason = reason
        self._body = body
        self._lines = lines or []
        self.text = "" if body is None else json.dumps(body)

    def json(self):
        if self._body is None:
            raise ValueError("No JSON body")
        return self._body

    def iter_lines(self):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def fake_request(monkeypatch, response=None, error=None):
    calls = []

    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if error:
            raise error
        return response

    monkeypatch.setattr(client_module.requests, "request", request)

    return calls


def test_parse_events_reads_bytes_and_text_and_skips_blank_lines():
    lines = [b'{"type": "token", "text": "A"}', b"", '{"type": "done"}', "  "]

    assert list(parse_events(lines)) == [
        {"type": "token", "text": "A"},
        {"type": "done"},
    ]


def test_stream_answer_yields_events_in_order(monkeypatch):
    calls = fake_request(
        monkeypatch,
        FakeResponse(lines=[
            b'{"type": "sources", "sources": []}',
            b'{"type": "token", "text": "Hi"}',
            b'{"type": "done", "retrieval_ms": 1, "generation_ms": 2}',
        ]),
    )

    events = list(ApiClient("http://api:8000/").stream_answer("Q?"))

    assert [event["type"] for event in events] == ["sources", "token", "done"]
    method, url, kwargs = calls[0]
    assert (method, url) == ("post", "http://api:8000/chat/stream")
    assert kwargs["json"] == {"question": "Q?"}
    assert kwargs["stream"] is True


def test_unreachable_api_raises_api_error(monkeypatch):
    fake_request(monkeypatch, error=requests.ConnectionError("refused"))

    with pytest.raises(ApiError, match="Cannot reach the API at http://api:8000"):
        ApiClient("http://api:8000").info()


def test_error_response_carries_the_api_detail(monkeypatch):
    fake_request(
        monkeypatch,
        FakeResponse(status_code=500, body={"detail": "Model unavailable"}),
    )

    with pytest.raises(ApiError, match="API error 500: Model unavailable"):
        list(ApiClient("http://api:8000").stream_answer("Q?"))


def test_upload_returns_the_api_message(monkeypatch):
    calls = fake_request(
        monkeypatch,
        FakeResponse(body={"message": "Document indexed successfully."}),
    )

    message = ApiClient("http://api:8000").upload("guide.pdf", b"PDF")

    assert message == "Document indexed successfully."
    assert calls[0][2]["files"]["file"] == ("guide.pdf", b"PDF", "application/pdf")


def test_rejected_upload_raises_with_the_reason(monkeypatch):
    fake_request(
        monkeypatch,
        FakeResponse(status_code=400, body={"detail": "Only PDF files can be uploaded."}),
    )

    with pytest.raises(ApiError, match="Only PDF files can be uploaded"):
        ApiClient("http://api:8000").upload("notes.txt", b"text")
