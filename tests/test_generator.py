
from types import SimpleNamespace
from unittest.mock import Mock

import generator as generator_module
from generator import Generator
from models import ChunkMetadata, RetrievedChunk


def make_chunk(document):
    return RetrievedChunk(
        document=document,
        metadata=ChunkMetadata(
            source="guide.pdf",
            page=1,
            chunk=0,
            heading="Introduction",
            level=1,
        ),
    )


def test_generate_sends_system_prompt_and_context_to_model(monkeypatch):
    client = Mock()
    client.chat.return_value = SimpleNamespace(
        message=SimpleNamespace(content="Python is a programming language.")
    )

    monkeypatch.setattr(
        generator_module,
        "Client",
        lambda host: client,
    )

    generator = Generator(
        model="test-model",
        host="http://test-host:11434",
    )

    answer = generator.generate(
        question="What is Python?",
        chunks=[make_chunk("Python is a programming language.")],
    )

    assert answer == "Python is a programming language."
    client.chat.assert_called_once()

    call = client.chat.call_args.kwargs
    assert call["model"] == "test-model"
    assert call["messages"][0]["role"] == "system"
    assert "ONLY the provided context" in call["messages"][0]["content"]
    assert call["messages"][1]["role"] == "user"
    assert "Python is a programming language." in call["messages"][1]["content"]
    assert "What is Python?" in call["messages"][1]["content"]


def test_build_prompt_includes_all_chunks_and_question(monkeypatch):
    monkeypatch.setattr(
        generator_module,
        "Client",
        lambda host: Mock(),
    )

    generator = Generator(model="test-model")

    prompt = generator._build_prompt(
        question="What are the features?",
        chunks=[
            make_chunk("Feature one."),
            make_chunk("Feature two."),
        ],
    )

    assert "Context:\n" in prompt
    assert "Feature one." in prompt
    assert "Feature two." in prompt
    assert "Question:\nWhat are the features?" in prompt
    assert prompt.endswith("Answer:")


def test_build_prompt_handles_empty_chunks(monkeypatch):
    monkeypatch.setattr(
        generator_module,
        "Client",
        lambda host: Mock(),
    )

    generator = Generator(model="test-model")

    prompt = generator._build_prompt(
        question="Unknown question",
        chunks=[],
    )

    assert "Context:\n\n" in prompt
    assert "Unknown question" in prompt
    assert prompt.endswith("Answer:")
