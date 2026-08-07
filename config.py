OLLAMA_HOST = "http://ollama:11434"
RERANK_MODEL = "BAAI/bge-reranker-base"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3"

CHROMA_PATH = "./data/chroma"
COLLECTION_NAME = "documents"

FINAL_TOP_K = 3
RETRIEVAL_TOP_K = max(FINAL_TOP_K * 4, 10)

MAX_CHUNK_SIZE = 1000

MIN_CHUNK_SIZE = 300

SIMILARITY_THRESHOLD = 0.88
