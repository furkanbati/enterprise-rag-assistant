import os


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
RERANK_MODEL = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3")

CHROMA_PATH = os.getenv("CHROMA_PATH", "./data/chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "documents")

FINAL_TOP_K = _env_int("FINAL_TOP_K", 3)
RETRIEVAL_TOP_K = _env_int("RETRIEVAL_TOP_K", max(FINAL_TOP_K * 4, 10))

MAX_CHUNK_SIZE = _env_int("MAX_CHUNK_SIZE", 1000)

MIN_CHUNK_SIZE = _env_int("MIN_CHUNK_SIZE", 300)

SIMILARITY_THRESHOLD = _env_float("SIMILARITY_THRESHOLD", 0.88)
