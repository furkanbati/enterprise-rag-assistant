# Enterprise RAG Assistant

A production-oriented Retrieval-Augmented Generation (RAG) assistant built with **FastAPI**, **Ollama**, **ChromaDB**, and **Docker**.

The project supports PDF ingestion, heading-aware semantic chunking, hybrid retrieval, Reciprocal Rank Fusion (RRF), cross-encoder reranking, and source-aware responses.

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

```text
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
6. Build the prompt using the highest-ranked chunks.
7. Generate the final answer using Llama 3.

---

# Document Ingestion Pipeline

```text
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

```text
enterprise-rag-assistant/
│
├── api.py
├── chunking.py
├── config.py
├── document_parser.py
├── embedder.py
├── generator.py
├── ingestion.py
├── models.py
├── pipeline.py
├── utils.py
├── vector_store.py
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

Exposes the REST API endpoints for document upload and question answering.

### pipeline.py

Coordinates the retrieval and answer-generation workflow.

### document_parser.py

Parses PDF documents with Docling and extracts structured document sections.

### chunking.py

Creates heading-aware semantic chunks using sentence-level embedding similarity.

### ingestion.py

Processes uploaded documents, generates embeddings, and stores chunks and metadata.

### embedder.py

Generates embeddings using Ollama.

### vector_store.py

Handles persistent ChromaDB storage and vector retrieval.

### generator.py

Generates final answers using Llama 3 through Ollama.

### retrieval/vector_search.py

Performs semantic vector retrieval.

### retrieval/keyword_search.py

Performs BM25 keyword retrieval.

### retrieval/fusion.py

Combines vector and keyword results using Reciprocal Rank Fusion.

### retrieval/reranker.py

Reranks retrieved chunks using a cross-encoder model.

### retrieval/retriever.py

Coordinates vector search, BM25 retrieval, result fusion, and reranking.

---

# Technology Stack

| Technology            | Purpose                          |
| --------------------- | -------------------------------- |
| Python                | Backend                          |
| FastAPI               | REST API                         |
| Ollama                | Local LLM and embedding provider |
| Llama 3               | Response generation              |
| nomic-embed-text      | Embedding model                  |
| ChromaDB              | Persistent vector database       |
| Docling               | PDF parsing                      |
| rank-bm25             | Keyword retrieval                |
| Sentence Transformers | Cross-encoder reranking          |
| Docker                | Containerization                 |

---

# Installation

## Clone the repository

```bash
git clone https://github.com/furkanbati/enterprise-rag-assistant.git
cd enterprise-rag-assistant
```

---

## Start the application

```bash
docker compose up --build -d
```

---

## Download the required Ollama models

Embedding model:

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

Chat model:

```bash
docker exec -it ollama ollama pull llama3
```

---

## Open Swagger UI

```text
http://localhost:8000/docs
```

---

# Usage

## Upload a PDF

```text
POST /upload
```

Example document:

```text
NIST.AI.100-1.pdf
```

The document is parsed, semantically chunked, embedded, and stored in ChromaDB.

---

## Ask a question

```text
POST /chat
```

Request:

```json
{
  "question": "Which AI RMF function enables the other functions?"
}
```

Example response:

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

The response includes source metadata and a preview of the retrieved supporting chunk.

---

# Configuration

Configuration is centralized in `config.py`.

Typical settings include:

* Chat model
* Embedding model
* Reranker model
* Chunk size
* Minimum chunk size
* Similarity threshold
* Retrieval top-k
* Final top-k
* ChromaDB storage path
* Collection name
* Ollama host

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

# Why Hybrid Retrieval?

Vector search is effective at semantic matching but may miss exact lexical matches.

BM25 is effective at keyword matching but does not capture semantic similarity.

Combining both approaches with Reciprocal Rank Fusion provides a broader candidate set, while cross-encoder reranking performs a final relevance-focused ranking before answer generation.

---

# Current Scope

The current implementation focuses on PDF-based document question answering using local Ollama inference.

The project currently does not include:

* Authentication and authorization
* Automated RAG evaluation and benchmarking
* Web-based user interface
* Persistent conversation history

These are intentionally outside the current scope and can be added in future iterations.

---

# Future Improvements

Possible future enhancements include:

* RAG evaluation and benchmarking
* Vector vs. hybrid vs. reranked retrieval comparison
* Query expansion
* Streaming responses
* Authentication and authorization
* Multi-format document support
* Multi-modal RAG
* Monitoring and observability

---

# License

This project is licensed under the MIT License. See the `LICENSE` file for details.
