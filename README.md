# Enterprise RAG Assistant

A production-ready Retrieval-Augmented Generation (RAG) assistant built with **FastAPI**, **Ollama**, **ChromaDB**, and **Docker**. The project supports PDF ingestion, heading-aware semantic chunking, hybrid retrieval, reranking, and source-aware responses.

---

# Features

* PDF document ingestion
* Heading-aware semantic chunking
* Metadata extraction (source, page, heading, chunk)
* Batch embedding generation
* Persistent ChromaDB vector storage
* Hybrid Retrieval (Vector Search + BM25)
* Reciprocal Rank Fusion (RRF)
* Cross-encoder reranking
* Source-aware answers
* Source preview snippets
* FastAPI REST API
* Swagger/OpenAPI documentation
* Dockerized deployment

---

# Architecture

```
                    +------------------+
                    |      Client      |
                    +------------------+
                              |
                              v
                      FastAPI REST API
                              |
                              v
                        RAG Pipeline
                              |
        +---------------------+----------------------+
        |                                            |
        v                                            v
 Question Embedding                         Document Ingestion
        |                                            |
        |                                    PDF Parsing
        |                                            |
        |                             Heading-aware Semantic Chunking
        |                                            |
        |                               Metadata Extraction
        |                                            |
        |                                Batch Embedding
        |                                            |
        |                                   ChromaDB Storage
        |
        v
+--------------------+
|  Vector Search     |
+--------------------+
          |
          |
+--------------------+
|    BM25 Search     |
+--------------------+
          |
          v
+----------------------------+
| Reciprocal Rank Fusion     |
+----------------------------+
          |
          v
+----------------------------+
| Cross Encoder Reranker     |
+----------------------------+
          |
          v
 Prompt Construction
          |
          v
      Llama 3
          |
          v
       Response
```

---

# Retrieval Pipeline

The retrieval pipeline combines semantic and lexical search to improve retrieval quality.

1. Generate an embedding for the user query.
2. Perform Vector Search on ChromaDB.
3. Perform BM25 keyword search.
4. Merge results using Reciprocal Rank Fusion (RRF).
5. Rerank retrieved documents using a Cross Encoder.
6. Build the prompt using the highest ranked chunks.
7. Generate the final answer using Llama 3.

---

# Document Ingestion Pipeline

```
PDF
 │
 ▼
Document Parsing
 │
 ▼
Heading-aware Semantic Chunking
 │
 ▼
Metadata Extraction
 │
 ▼
Batch Embedding Generation
 │
 ▼
Persistent ChromaDB Storage
```

Each stored chunk includes metadata such as:

* Source document
* Page number
* Section heading
* Chunk identifier

---

# Project Structure

```
enterprise-rag-assistant/
│
├── api.py
├── config.py
├── embedder.py
├── generator.py
├── ingestion.py
├── parser.py
├── pipeline.py
├── vector_store.py
├── models.py
│
├── retrieval/
│   ├── vector_search.py
│   ├── keyword_search.py
│   ├── fusion.py
│   ├── reranker.py
│   └── retriever.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# Module Overview

### api.py

Exposes the REST API endpoints.

### pipeline.py

Coordinates the complete RAG workflow.

### parser.py

Parses PDF documents and extracts structured sections.

### ingestion.py

Processes uploaded documents and stores them into the vector database.

### embedder.py

Generates embeddings using Ollama.

### vector_store.py

Handles ChromaDB storage and retrieval.

### generator.py

Generates final answers using Llama 3.

### retrieval/vector_search.py

Performs semantic vector retrieval.

### retrieval/keyword_search.py

Performs BM25 keyword retrieval.

### retrieval/fusion.py

Combines search results using Reciprocal Rank Fusion.

### retrieval/reranker.py

Ranks retrieved chunks using a Cross Encoder.

### retrieval/retriever.py

Coordinates the complete retrieval pipeline.

---

# Technology Stack

| Technology             | Purpose                |
| ---------------------- | ---------------------- |
| Python                 | Backend                |
| FastAPI                | REST API               |
| Ollama                 | Local LLM & Embeddings |
| Llama 3                | Response generation    |
| nomic-embed-text       | Embedding model        |
| ChromaDB               | Vector database        |
| Docling                | PDF parsing            |
| rank-bm25              | Keyword retrieval      |
| Cross Encoder Reranker | Result reranking       |
| Docker                 | Containerization       |

---

# Installation

## Clone the repository

```bash
git clone https://github.com/<your-username>/enterprise-rag-assistant.git
cd enterprise-rag-assistant
```

---

## Start the application

```bash
docker compose up --build -d
```

---

## Download the required Ollama models

Embedding model

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

Chat model

```bash
docker exec -it ollama ollama pull llama3
```

---

## Open Swagger UI

```
http://localhost:8000/docs
```

---

# Usage

## Upload a PDF

```
POST /upload
```

Example:

```
NIST.AI.100-1.pdf
```

---

## Ask a question

```
POST /chat
```

Request

```json
{
  "question": "Which AI RMF function enables the other functions?"
}
```

Response

```json
{
  "answer": "The answer is GOVERN.",
  "sources": [
    {
      "source": "NIST.AI.100-1.pdf",
      "page": 25,
      "chunk": 133,
      "heading": "5. AI RMF Core",
      "preview": "After instituting the outcomes in GOVERN..."
    }
  ]
}
```

---

# Configuration

Configuration is centralized in `config.py`.

Typical settings include:

* Chat model
* Embedding model
* Chunk size
* Chunk overlap
* Vector search top-k
* BM25 top-k
* Reranker top-k
* ChromaDB storage path
* Collection name
* Ollama host
* Logging level

---

# Current Capabilities

* Semantic document retrieval
* Heading-aware semantic chunking
* Metadata-aware indexing
* Hybrid retrieval
* Reciprocal Rank Fusion
* Cross-encoder reranking
* Source-aware responses
* Source preview generation
* Persistent vector storage
* Docker deployment
* REST API
* Interactive Swagger documentation

---

# Future Improvements

Possible future enhancements include:

* Query expansion
* Streaming responses
* Evaluation pipeline (RAGAS / DeepEval)
* Authentication & authorization
* Multi-format document support
* Multi-modal RAG
* Monitoring & observability

---

# Why Hybrid Retrieval?

Vector search excels at semantic similarity but may miss exact keyword matches.

BM25 excels at lexical matching but lacks semantic understanding.

By combining both approaches with Reciprocal Rank Fusion and a Cross Encoder reranker, the assistant achieves significantly more reliable retrieval quality.

---

# License

This project is intended for educational and portfolio purposes. Feel free to modify and extend it for your own use.
