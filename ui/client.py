"""HTTP client for the RAG API, kept free of Streamlit so it can be tested."""

import json
from collections.abc import Iterable, Iterator

import requests

CONNECT_TIMEOUT_SECONDS = 10
# Local models can take minutes to answer, especially on a cold start.
ANSWER_TIMEOUT_SECONDS = 600


class ApiError(Exception):
    """The API could not be reached or returned an error."""


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def info(self) -> dict:
        response = self._request(
            "get",
            "/info",
            timeout=CONNECT_TIMEOUT_SECONDS,
        )

        return response.json()

    def upload(self, filename: str, content: bytes) -> str:
        response = self._request(
            "post",
            "/upload",
            files={"file": (filename, content, "application/pdf")},
            timeout=(CONNECT_TIMEOUT_SECONDS, ANSWER_TIMEOUT_SECONDS),
        )

        return response.json()["message"]

    def stream_answer(self, question: str) -> Iterator[dict]:
        """Yield the events of POST /chat/stream as they arrive."""

        response = self._request(
            "post",
            "/chat/stream",
            json={"question": question},
            stream=True,
            timeout=(CONNECT_TIMEOUT_SECONDS, ANSWER_TIMEOUT_SECONDS),
        )

        with response:
            try:
                yield from parse_events(response.iter_lines())
            except requests.RequestException as e:
                raise ApiError(f"The answer stream was interrupted: {e}") from e

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"

        try:
            response = requests.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise ApiError(f"Cannot reach the API at {self.base_url}: {e}") from e

        if not response.ok:
            raise ApiError(_error_detail(response))

        return response


def parse_events(lines: Iterable[bytes | str]) -> Iterator[dict]:
    """Parse newline-delimited JSON events, skipping blank lines."""

    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("utf-8")

        if line.strip():
            yield json.loads(line)


def _error_detail(response: requests.Response) -> str:
    try:
        detail = response.json()["detail"]
    except (ValueError, KeyError, TypeError):
        detail = response.text or response.reason

    return f"API error {response.status_code}: {detail}"
