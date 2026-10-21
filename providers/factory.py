from openai import OpenAI

from config import (
    OLLAMA_HOST,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_REASONING_EFFORT,
)
from providers.base import ChatClient, Embedder
from providers.ollama import OllamaChatClient, OllamaEmbedder
from providers.openai import OpenAIChatClient, OpenAIEmbedder

PROVIDERS = ("ollama", "openai")

# The SDK default of ten minutes is too long for a web request.
OPENAI_TIMEOUT_SECONDS = 60.0


def build_embedder(provider: str, model: str) -> Embedder:
    if provider == "ollama":
        return OllamaEmbedder(model=model, host=OLLAMA_HOST)

    if provider == "openai":
        return OpenAIEmbedder(client=_openai_client(), model=model)

    raise ValueError(_unknown_provider("embedding", provider))


def build_chat_client(provider: str, model: str) -> ChatClient:
    if provider == "ollama":
        return OllamaChatClient(model=model, host=OLLAMA_HOST)

    if provider == "openai":
        return OpenAIChatClient(
            client=_openai_client(),
            model=model,
            reasoning_effort=OPENAI_REASONING_EFFORT,
        )

    raise ValueError(_unknown_provider("LLM", provider))


def _openai_client() -> OpenAI:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY must be set when a provider is 'openai'."
        )

    return OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=OPENAI_TIMEOUT_SECONDS,
    )


def _unknown_provider(kind: str, provider: str) -> str:
    choices = " or ".join(f"'{name}'" for name in PROVIDERS)
    return f"Unknown {kind} provider '{provider}'. Use {choices}."
