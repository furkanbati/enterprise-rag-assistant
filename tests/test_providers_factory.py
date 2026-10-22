
import pytest

import providers.factory as factory
from providers.ollama import OllamaChatClient, OllamaEmbedder
from providers.openai import OpenAIChatClient, OpenAIEmbedder


def test_builds_ollama_clients():
    assert isinstance(
        factory.build_embedder(provider="ollama", model="nomic-embed-text"),
        OllamaEmbedder,
    )
    assert isinstance(
        factory.build_chat_client(provider="ollama", model="llama3"),
        OllamaChatClient,
    )


def test_builds_openai_clients_when_key_is_set(monkeypatch):
    monkeypatch.setattr(factory, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(factory, "OPENAI_REASONING_EFFORT", "low")

    embedder = factory.build_embedder(
        provider="openai",
        model="text-embedding-3-small",
    )
    chat = factory.build_chat_client(provider="openai", model="gpt-6-luna")

    assert isinstance(embedder, OpenAIEmbedder)
    assert embedder.model == "text-embedding-3-small"
    assert isinstance(chat, OpenAIChatClient)
    assert chat.model == "gpt-6-luna"
    assert chat.reasoning_effort == "low"


def test_passes_base_url_to_openai_client(monkeypatch):
    monkeypatch.setattr(factory, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(factory, "OPENAI_BASE_URL", "http://compatible.test/v1")

    chat = factory.build_chat_client(provider="openai", model="some-model")

    assert str(chat.client.base_url).startswith("http://compatible.test/v1")


def test_openai_requires_api_key(monkeypatch):
    monkeypatch.setattr(factory, "OPENAI_API_KEY", "")

    with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
        factory.build_chat_client(provider="openai", model="gpt-6-luna")

    with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
        factory.build_embedder(provider="openai", model="text-embedding-3-small")


def test_unknown_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown LLM provider 'anthropic'"):
        factory.build_chat_client(provider="anthropic", model="x")

    with pytest.raises(ValueError, match="Unknown embedding provider 'x'"):
        factory.build_embedder(provider="x", model="y")
