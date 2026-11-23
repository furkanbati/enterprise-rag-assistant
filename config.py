import os


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return value.strip().lower() in ("1", "true", "yes", "on") if value else default


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "ollama")

_DEFAULT_CHAT_MODELS = {"ollama": "llama3", "openai": "gpt-6-luna"}
_DEFAULT_EMBED_MODELS = {"ollama": "nomic-embed-text", "openai": "text-embedding-3-small"}

CHAT_MODEL = os.getenv("CHAT_MODEL") or _DEFAULT_CHAT_MODELS.get(LLM_PROVIDER, "")

# Turkish questions are answered by a multilingual model on Ollama: llama3
# answers most Turkish questions in English. Other providers use CHAT_MODEL.
_DEFAULT_CHAT_MODELS_TR = {"ollama": "qwen3.5:4b"}


def chat_model_tr(provider: str, chat_model: str, override: str | None) -> str:
    """The chat model for Turkish questions: CHAT_MODEL_TR when set, else
    the provider's Turkish default, else the chat model."""

    return override or _DEFAULT_CHAT_MODELS_TR.get(provider) or chat_model


CHAT_MODEL_TR = chat_model_tr(LLM_PROVIDER, CHAT_MODEL, os.getenv("CHAT_MODEL_TR"))
EMBED_MODEL = os.getenv("EMBED_MODEL") or _DEFAULT_EMBED_MODELS.get(EMBED_PROVIDER, "")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
# Reasoning of thinking chat models (e.g. qwen3.5): empty keeps the model's
# default; true / false, or low / medium / high on models with levels.
OLLAMA_THINK = os.getenv("OLLAMA_THINK", "")
# The same for the Turkish chat model. Off by default: qwen3.5 thinks until
# it fills the context on a CPU. Models without thinking accept false.
OLLAMA_THINK_TR = os.getenv("OLLAMA_THINK_TR", "false")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low") or None

# Model that grades generated answers in the evaluations (python -m evaluation
# --judge and python -m evaluation.ragas_eval). A stronger model than the one
# answering avoids grading itself.
JUDGE_PROVIDER = os.getenv("JUDGE_PROVIDER", "openai")
_DEFAULT_JUDGE_MODELS = {"ollama": "llama3", "openai": "gpt-6.1-sol"}
JUDGE_MODEL = os.getenv("JUDGE_MODEL") or _DEFAULT_JUDGE_MODELS.get(JUDGE_PROVIDER, "")

# Embedding model RAGAS uses for answer relevancy; defaults to the
# application's embedding model.
RAGAS_EMBED_PROVIDER = os.getenv("RAGAS_EMBED_PROVIDER") or EMBED_PROVIDER
RAGAS_EMBED_MODEL = os.getenv("RAGAS_EMBED_MODEL") or (
    EMBED_MODEL
    if RAGAS_EMBED_PROVIDER == EMBED_PROVIDER
    else _DEFAULT_EMBED_MODELS.get(RAGAS_EMBED_PROVIDER, "")
)

RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
# Turkish questions use their own reranker: the default one is English-only
# and pushes the right Turkish passage down. Set it to the same value as
# RERANK_MODEL to use one reranker for both languages.
RERANK_MODEL_TR = os.getenv(
    "RERANK_MODEL_TR", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")

FINAL_TOP_K = _env_int("FINAL_TOP_K", 3)
RETRIEVAL_TOP_K = _env_int("RETRIEVAL_TOP_K", max(FINAL_TOP_K * 4, 10))

CHUNKING_STRATEGY = os.getenv("CHUNKING_STRATEGY", "sentence")

# Prefix every chunk with the document title, so that search can tell apart
# documents with similar content.
CHUNK_CONTEXT = _env_bool("CHUNK_CONTEXT", True)

# Used by the semantic strategy only.
SEMANTIC_PERCENTILE = _env_int("SEMANTIC_PERCENTILE", 90)
SEMANTIC_WINDOW = _env_int("SEMANTIC_WINDOW", 1)

MAX_CHUNK_SIZE = _env_int("MAX_CHUNK_SIZE", 1000)

MIN_CHUNK_SIZE = _env_int("MIN_CHUNK_SIZE", 300)

# OCR engine for PDFs without a text layer: "rapidocr", "easyocr" or "off".
OCR_ENGINE = os.getenv("OCR_ENGINE", "rapidocr")
