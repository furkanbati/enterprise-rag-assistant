
from types import SimpleNamespace
from unittest.mock import Mock

import providers.ollama as ollama_module
from providers.ollama import OllamaChatClient, OllamaEmbedder


def patch_client(monkeypatch, client):
    hosts = []

    def make_client(host):
        hosts.append(host)
        return client

    monkeypatch.setattr(ollama_module, "Client", make_client)

    return hosts


def test_chat_client_sends_model_and_messages(monkeypatch):
    client = Mock()
    client.chat.return_value = SimpleNamespace(
        message=SimpleNamespace(content="Python is a programming language.")
    )
    hosts = patch_client(monkeypatch, client)

    chat = OllamaChatClient(
        model="test-model",
        host="http://test-host:11434",
    )

    reply = chat.complete(system="System prompt.", user="What is Python?")

    assert reply == "Python is a programming language."
    assert hosts == ["http://test-host:11434"]
    client.chat.assert_called_once_with(
        model="test-model",
        messages=[
            {"role": "system", "content": "System prompt."},
            {"role": "user", "content": "What is Python?"},
        ],
    )


def test_embedder_embeds_single_text(monkeypatch):
    client = Mock()
    client.embed.return_value = SimpleNamespace(embeddings=[[0.1, 0.2]])
    patch_client(monkeypatch, client)

    embedder = OllamaEmbedder(model="embed-model")

    assert embedder.embed("hello") == [0.1, 0.2]
    client.embed.assert_called_once_with(model="embed-model", input="hello")


def test_embedder_embeds_batch(monkeypatch):
    client = Mock()
    client.embed.return_value = SimpleNamespace(embeddings=[[0.1], [0.2]])
    patch_client(monkeypatch, client)

    embedder = OllamaEmbedder(model="embed-model")

    assert embedder.embed_batch(["a", "b"]) == [[0.1], [0.2]]
    client.embed.assert_called_once_with(model="embed-model", input=["a", "b"])
