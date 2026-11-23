import pytest

from config import chat_model_tr


@pytest.mark.parametrize(
    ("provider", "chat_model", "override", "expected"),
    [
        # Ollama: a multilingual model answers Turkish questions by default.
        ("ollama", "llama3", None, "qwen3.5:4b"),
        ("ollama", "llama3", "", "qwen3.5:4b"),
        # An explicit CHAT_MODEL_TR always wins.
        ("ollama", "llama3", "gemma3:12b", "gemma3:12b"),
        ("ollama", "llama3", "llama3", "llama3"),
        # Other providers keep their chat model for Turkish too.
        ("openai", "gpt-6-luna", None, "gpt-6-luna"),
        ("openai", "gpt-6-luna", "gpt-6-sol", "gpt-6-sol"),
    ],
)
def test_chat_model_tr(provider, chat_model, override, expected):
    assert chat_model_tr(provider, chat_model, override) == expected
