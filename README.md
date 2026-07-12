# Enterprise RAG Assistant

A lightweight, containerized Retrieval-Augmented Generation (RAG) backend built with FastAPI, Ollama, and ChromaDB.

The system ingests PDF documents, converts their content into vector embeddings, stores them in a persistent vector database, retrieves relevant document context for user questions, and generates grounded answers using a locally hosted Large Language Model.

The project focuses on a simple and explicit architecture without unnecessary abstraction layers.

## Architecture

```text
                        ┌──────────────────────┐
                        │        Client        │
                        │   Swagger / HTTP     │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │       FastAPI        │
                        │        api.py        │
                        └──────────┬───────────┘
                                   │
                 ┌─────────────────┴─────────────────┐
                 │                                   │
                 ▼                                   ▼
        Document Ingestion                      RAG Pipeline
                 │                                   │
                 ▼                                   ▼
        PDF Text Extraction                         Query
                 │                                   │
                 ▼                                   ▼
             Chunking                            Embedder
                 │                                   │
                 ▼                                   ▼
             Embedder                            Retriever
                 │                                   │
                 ▼                                   ▼
        Ollama Embedding Model                    ChromaDB
                 │                                   │
                 ▼                                   ▼
             ChromaDB                      Relevant Documents
                                                     │
                                                     ▼
                                                  Generator
                                                     │
                                                     ▼
                                             Ollama Chat Model
                                                     │
                                                     ▼
                                                   Answer
```

## RAG Workflow

### Document ingestion

When a PDF document is uploaded:

```text
PDF
 ↓
Text Extraction
 ↓
Chunking
 ↓
Batch Embedding
 ↓
Vector Storage
```

The ingestion layer extracts text from the PDF using PyMuPDF.

The extracted text is divided into overlapping chunks. Each chunk is converted into a vector embedding using the configured Ollama embedding model.

The documents and their embeddings are then persisted in ChromaDB.

### Question answering

When a user submits a question:

```text
Question
 ↓
Query Embedding
 ↓
Vector Search
 ↓
Relevant Documents
 ↓
Prompt Construction
 ↓
LLM Generation
 ↓
Answer
```

The question is embedded using the same embedding model used during ingestion.

The retriever searches ChromaDB for semantically relevant document chunks.

The generator combines the retrieved context with the original question and sends the resulting prompt to the configured Ollama chat model.

The generated answer is returned through the API.

## Project Structure

```text
enterprise_rag_v2/
│
├── api.py
├── config.py
├── embedder.py
├── generator.py
├── ingestion.py
├── pipeline.py
├── retriever.py
├── vector_store.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── README.md
```

### `api.py`

Application entry point and composition root.

Responsible for:

* Creating the FastAPI application
* Initializing application dependencies
* Connecting configuration values to application components
* Exposing document upload and chat endpoints

### `config.py`

Central application configuration.

Controls:

* Embedding model
* Chat model
* Ollama host
* Chunk size
* Chunk overlap
* ChromaDB persistence path
* ChromaDB collection name

Application behavior can be changed without modifying the core modules.

### `embedder.py`

Handles communication with the Ollama embedding API.

Supports:

* Single-text embedding
* Batch embedding

### `ingestion.py`

Handles the document indexing workflow.

Responsible for:

* PDF text extraction
* Text chunking
* Chunk overlap
* Batch embedding
* Vector storage

### `vector_store.py`

Encapsulates ChromaDB operations.

Responsible for:

* Persistent vector storage
* Document insertion
* Semantic vector queries

### `retriever.py`

Retrieves relevant document chunks from the vector store using a query embedding.

### `generator.py`

Builds the RAG prompt and communicates with the Ollama chat model.

The generator receives:

```text
Question
+
Retrieved Documents
```

and produces a grounded answer based on the retrieved context.

### `pipeline.py`

Coordinates the question-answering workflow.

```text
Embed Question
      ↓
Retrieve Documents
      ↓
Generate Answer
```

The pipeline keeps orchestration separate from infrastructure-specific logic.

## Technology Stack

| Technology       | Purpose                       |
| ---------------- | ----------------------------- |
| Python           | Application language          |
| FastAPI          | HTTP API                      |
| Ollama           | Local model runtime           |
| Llama 3          | Answer generation             |
| nomic-embed-text | Vector embeddings             |
| ChromaDB         | Vector database               |
| PyMuPDF          | PDF text extraction           |
| Docker           | Application containerization  |
| Docker Compose   | Multi-container orchestration |

## Requirements

The only host dependency required is:

* Docker Desktop

Python and Ollama do not need to be installed directly on the host machine.

## Running the Project

Clone the repository:

```bash
git clone <repository-url>
cd enterprise_rag_v2
```

Build and start the containers:

```bash
docker compose up --build -d
```

Verify that the containers are running:

```bash
docker ps
```

The following containers should be available:

```text
rag-api
ollama
```

## Download Ollama Models

The application uses two models.

Embedding model:

```text
nomic-embed-text
```

Chat model:

```text
llama3
```

Download the models inside the Ollama container:

```bash
docker exec -it ollama ollama pull nomic-embed-text
```

```bash
docker exec -it ollama ollama pull llama3
```

Verify the installed models:

```bash
docker exec -it ollama ollama list
```

Expected models:

```text
nomic-embed-text
llama3
```

## API Documentation

After the containers are running, open the FastAPI Swagger interface:

```text
http://localhost:8000/docs
```

The API currently exposes two main endpoints.

## Upload a Document

```text
POST /upload
```

Uploads and indexes a PDF document.

The document passes through the complete ingestion pipeline:

```text
PDF
 ↓
Extract Text
 ↓
Chunk Text
 ↓
Generate Embeddings
 ↓
Store in ChromaDB
```

Example response:

```json
{
  "message": "Document indexed successfully."
}
```

## Ask a Question

```text
POST /chat
```

Example request:

```json
{
  "question": "What are the core functions of the AI RMF?"
}
```

Example response:

```json
{
  "answer": "The AI RMF Core provides four high-level functions: GOVERN, MAP, MEASURE, and MANAGE."
}
```

The answer is generated using document chunks retrieved from ChromaDB.

## Configuration

Application configuration is centralized in `config.py`.

Example:

```python
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3"

CHUNK_SIZE = 1000
OVERLAP = 200

CHROMA_PATH = "./data/chroma"
COLLECTION_NAME = "documents"

OLLAMA_HOST = "http://ollama:11434"
```

For example, changing the chat model only requires updating:

```python
CHAT_MODEL = "llama3"
```

Core application modules do not need to be modified.

## Persistent Storage

ChromaDB data is persisted on the host machine:

```text
./data/chroma
```

Ollama models are stored in a Docker volume:

```text
ollama
```

Stopping or recreating the containers does not require downloading the models again.

## Useful Docker Commands

Start the application:

```bash
docker compose up -d
```

Rebuild after code changes:

```bash
docker compose up --build -d
```

View API logs:

```bash
docker compose logs -f api
```

View all logs:

```bash
docker compose logs -f
```

Stop and remove the containers:

```bash
docker compose down
```

List running containers:

```bash
docker ps
```

List installed Ollama models:

```bash
docker exec -it ollama ollama list
```

## Design Principles

This project intentionally follows a small set of architectural principles:

* Explicit dependency construction
* Centralized configuration
* Minimal abstraction
* Clear module responsibilities
* Persistent vector storage
* Local model execution
* Containerized runtime
* Independently replaceable RAG components

The architecture avoids unnecessary framework layers and keeps the complete RAG workflow visible in the codebase.

## Current Capabilities

* PDF document ingestion
* PDF text extraction
* Overlapping text chunking
* Batch embedding generation
* Persistent vector storage
* Semantic document retrieval
* Context-based prompt generation
* Local LLM inference
* REST API
* Swagger API documentation
* Dockerized deployment

## Roadmap

Planned improvements include:

* Retrieval score visibility
* Retrieval quality evaluation
* Document metadata
* Source-aware responses
* Duplicate document handling
* Improved document validation
* Configurable retrieval limits
* Health checks
* Automated tests
* RAG evaluation pipeline

## License

This project is available for educational, research, and development purposes.
