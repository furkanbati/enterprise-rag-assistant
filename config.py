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
EMBED_MODEL = os.getenv("EMBED_MODEL") or _DEFAULT_EMBED_MODELS.get(EMBED_PROVIDER, "")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "low") or None

# Model that grades generated answers in the evaluation (python -m evaluation
# --judge). A stronger model than the one answering avoids grading itself.
JUDGE_PROVIDER = os.getenv("JUDGE_PROVIDER", "openai")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-6.1-sol")

RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

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
