# Enterprise RAG Assistant

[![CI](https://github.com/furkanbati/enterprise-rag-assistant/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/furkanbati/enterprise-rag-assistant/actions/workflows/ci.yml)

A document question-answering system built with **Python, FastAPI, ChromaDB, Ollama, and Docker**.

The application ingests PDF, Word, HTML, Markdown and text documents, retrieves relevant passages using hybrid search, reranks the results, and generates answers with source metadata and text previews.

It demonstrates an end-to-end Retrieval-Augmented Generation (RAG) workflow, from document ingestion to grounded question answering.

![The web interface answering a question about the NIST Cybersecurity Framework, with the three source passages it used](docs/ui.png)

## Key Features

- Ingestion of PDF, DOCX, HTML, Markdown and plain-text files, with structured parsing by Docling
- Document management: re-uploading a file replaces its earlier version, and documents can be listed and removed
- Heading-aware, sentence-aligned chunking that keeps each chunk's document title, with an optional semantic chunker evaluated against it
- Metadata extraction for document source, page, heading, and chunk
- Batch embedding generation with Ollama or OpenAI
- Local (Ollama) or cloud (OpenAI) models, selected per role with environment variables
- Persistent vector storage with ChromaDB
- Hybrid retrieval using vector search and BM25
- Reciprocal Rank Fusion (RRF) for combining retrieval results
- Cross-encoder reranking
- Answers cite the passages they use with numbered references, linked to source cards with page metadata and previews
- FastAPI REST endpoints, including a streaming chat endpoint, and interactive Swagger documentation
- Streamlit chat interface with streamed answers, source previews and timings
- Docker Compose-based application setup
- Built-in evaluation harness comparing retrieval strategies and scoring generated answers, with an optional LLM judge for correctness, grounding and citation support

## Architecture

```text
                     PDF Document
                          |
                          v
                  Document Ingestion
                          |
                    Docling Parser
                          |
                          v
        Heading-aware, Sentence-aligned Chunking
                          |
                          v
                 Metadata Extraction
                          |
                          v
                  Batch Embeddings
                          |
                          v
                    ChromaDB
                          |
                          |
User Question             |
      |                   |
      v                   |
Query Embedding           |
      |                   |
      +--------+----------+
               |
        +------+------+
        |             |
        v             v
   Vector Search   BM25 Search
        |             |
        +------+------+
               |
               v
       Reciprocal Rank Fusion
               |
               v
        Cross-Encoder Reranking
               |
               v
       Context and Prompt Construction
               |
               v
  Chat Model (Ollama or OpenAI)
               |
               v
     Answer + Source Metadata
```

## How It Works

### 1. Document ingestion

A PDF is submitted through the API. Docling parses the document into sections, and the chunking component packs the whole sentences of each section into chunks of roughly 300 to 1000 characters, prefixed with the document title and the section heading. Each chunk retains metadata such as its source document, page, heading, and chunk identifier. See [Chunking](#chunking) for the semantic alternative and how the two compare.

### 2. Embedding and storage

The configured embedding provider (Ollama by default, or OpenAI) generates embeddings for the chunks. ChromaDB stores the document content, embeddings, and associated metadata for later retrieval.

### 3. Hybrid retrieval

When a user submits a question:

1. The question is converted into an embedding.
2. ChromaDB retrieves semantically similar chunks.
3. BM25 retrieves keyword-relevant chunks.
4. Reciprocal Rank Fusion combines the ranked results.
5. A cross-encoder reranks the candidates by relevance.

### 4. Answer generation

The highest-ranked chunks are passed to the configured chat model (Ollama by default, or OpenAI). The API returns the generated answer along with source metadata and text previews to help users inspect the retrieved context. The passages are numbered in the prompt, and the model cites them after each statement as [1], [2] and so on; [n] refers to the n-th entry of the returned sources.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| FastAPI | REST API |
| Streamlit | Web chat interface |
| Docling | PDF parsing |
| Ollama | Local model inference and embeddings |
| OpenAI API | Optional cloud chat and embedding models |
| Llama 3 | Answer generation |
| nomic-embed-text | Text embeddings |
| ChromaDB | Persistent vector storage |
| rank-bm25 | Lexical retrieval |
| Sentence Transformers | Cross-encoder reranking |
| Docker Compose | Container orchestration |
| pytest | Automated testing |

## Getting Started

### Prerequisites

- Docker Desktop with Docker Compose
- Sufficient memory and disk space for the local models
- Internet access for the initial model downloads

### 1. Clone the repository

```bash
git clone https://github.com/furkanbati/enterprise-rag-assistant.git
cd enterprise-rag-assistant
```

### 2. Start the services

```bash
docker compose up --build -d
```

### 3. Download the required Ollama models

```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull llama3
```

The cross-encoder model is configured as `cross-encoder/ms-marco-MiniLM-L-6-v2` and is loaded when reranking is first needed. Its initial use may require downloading the model.

### 4. Open the web interface

Once the services are running, open:

**http://localhost:8501**

Upload a document from the sidebar, then ask questions in the chat. The sources appear as soon as retrieval is done, the answer streams in token by token, and each answer lists its sources and the retrieval and generation times.

The interactive API documentation is available at **http://localhost:8000/docs**. Both services are published on `localhost` only, so they are not reachable from other devices on the network.

## API Usage

### Upload a document

Endpoint:

```http
POST /upload
```

The endpoint accepts `.pdf`, `.docx`, `.html`, `.htm`, `.md` and `.txt` files, processes their content, generates embeddings, and indexes the chunks in ChromaDB. Other file types are rejected with status 400, and a file with no extractable text with status 422. A PDF without a text layer, such as a scan, is read a second time with OCR (RapidOCR through Docling by default; see `OCR_ENGINE`) before it is rejected; OCR is skipped for PDFs that already contain text because it is much slower. The upload is written to a temporary directory and removed once it is indexed.

Uploading a file with the same name as an indexed document replaces it. The new version is parsed and embedded first, and the old chunks are removed only then, so a file that fails to process leaves the indexed version untouched. The response reports the result:

```json
{
  "message": "Document indexed successfully.",
  "source": "NIST.CSWP.29.pdf",
  "chunks": 124,
  "replaced": true
}
```

Formats without pages (DOCX, HTML, Markdown, text) report every source on page 1.

### Manage documents

```http
GET /documents
DELETE /documents/{source}
```

`GET /documents` lists the indexed documents with their number of chunks. `DELETE /documents/{source}` removes a document and all of its chunks, and returns 404 for an unknown name. The web interface offers the same actions in its sidebar.

### Ask a question

Endpoint:

```http
POST /chat
Content-Type: application/json
```

Example request:

```json
{
  "question": "What are the four core functions of the NIST AI Risk Management Framework?"
}
```

Example response shape:

```json
{
  "answer": "The four core functions are GOVERN, MAP, MEASURE, and MANAGE. [1]",
  "sources": [
    {
      "source": "nist.ai.100-1.pdf",
      "page": 6,
      "chunk": 27,
      "heading": "Executive Summary",
      "preview": "It describes four specific functions to help organizations address the risks of AI systems in practice..."
    }
  ]
}
```

The response above illustrates the API response format. Actual answers, source ordering, and preview text depend on the uploaded documents and retrieval results. Citations such as [1] in the answer refer to the entries of `sources` in order, starting at 1.

### Stream an answer

Endpoint:

```http
POST /chat/stream
Content-Type: application/json
```

The request is the same as for `POST /chat`. The response is newline-delimited JSON (`application/x-ndjson`), one event per line:

```text
{"type": "sources", "sources": [{"source": "nist.ai.100-1.pdf", "page": 6, ...}]}
{"type": "token", "text": "The four core"}
{"type": "token", "text": " functions are"}
...
{"type": "done", "retrieval_ms": 612, "generation_ms": 6909}
```

The sources are sent as soon as retrieval is done, before the model starts writing. If anything fails, the stream ends with `{"type": "error", "detail": "..."}` instead of `done`.

### Inspect the configuration

```http
GET /info
```

Returns the active models, the chunking configuration and the indexed documents:

```json
{
  "chat_model": "ollama/llama3",
  "embedding_model": "ollama/nomic-embed-text",
  "chunking": "sentence",
  "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
  "documents": [
    {"source": "nist.ai.100-1.pdf", "chunks": 221}
  ]
}
```

## Configuration

Settings live in `config.py` and can be overridden with environment variables or a `.env` file (see [`.env.example`](.env.example)).

| Setting | Purpose |
|---|---|
| `LLM_PROVIDER` | `ollama` (default) or `openai` |
| `EMBED_PROVIDER` | `ollama` (default) or `openai` |
| `CHAT_MODEL` | Answer-generation model; defaults to `llama3` for Ollama and `gpt-6-luna` for OpenAI |
| `EMBED_MODEL` | Embedding model; defaults to `nomic-embed-text` for Ollama and `text-embedding-3-small` for OpenAI |
| `OLLAMA_HOST` | Ollama service URL |
| `OPENAI_API_KEY` | Required when a provider is `openai` |
| `OPENAI_BASE_URL` | Optional: any OpenAI-compatible API |
| `OPENAI_REASONING_EFFORT` | Reasoning effort for OpenAI reasoning models (default `low`; empty to omit) |
| `RERANK_MODEL` | Cross-encoder reranking model |
| `CHROMA_PATH` | Persistent vector database path |
| `COLLECTION_NAME` | Base name of the ChromaDB collection; the embedding model and chunking configuration are appended, so each combination has its own collection |
| `RETRIEVAL_TOP_K` | Number of candidates retrieved |
| `FINAL_TOP_K` | Number of chunks retained after reranking |
| `CHUNKING_STRATEGY` | `sentence` (default) or `semantic` |
| `CHUNK_CONTEXT` | Prefix every chunk with its document title (default `true`); see [Chunking](#chunking) |
| `MAX_CHUNK_SIZE` | Maximum chunk size in characters, unless a single sentence is longer |
| `MIN_CHUNK_SIZE` | Minimum chunk size in characters |
| `SEMANTIC_PERCENTILE` | Semantic chunking: split at boundaries above this percentile of embedding distances in the document |
| `SEMANTIC_WINDOW` | Semantic chunking: sentences on each side embedded with each sentence |
| `OCR_ENGINE` | OCR for PDFs without a text layer: `rapidocr` (default), `easyocr` or `off`. On two scanned pages RapidOCR took about 9 s per page and EasyOCR about 27 s |

The default configuration uses the Ollama service provided by Docker Compose.

## Model Providers

The chat model and the embedding model are chosen independently. To answer with OpenAI, add the key and the providers to `.env` and restart the API:

```dotenv
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
EMBED_PROVIDER=openai
```

Switching the chat provider takes effect immediately. Each embedding model has its own collection, so after switching the embedding provider the documents have to be uploaded again. A missing key or an unknown provider stops the API at startup with a clear message.

### Local vs cloud

Measured on 2026-10-22 on the NIST AI RMF question set (20 answerable, 2 unanswerable), with the AI RMF, CSF 2.0 and FOMC transcript indexed, sentence chunking and the same cross-encoder reranker.

| | Local (Ollama) | Cloud (OpenAI) |
|---|---|---|
| Models | `llama3` + `nomic-embed-text` | `gpt-6-luna` + `text-embedding-3-small` |
| MRR, vector search only | 0.950 | 0.892 |
| MRR, full pipeline | **1.000** | **1.000** |
| Answer rate / abstention rate | 1.000 / 1.000 | 1.000 / 1.000 |
| Keyword recall | 0.950 | 0.875 |
| Mean generation time | 12.4 s (CPU) | **1.3 s** |
| Cost per question | none | < $0.0002 (6,241 chat tokens for 22 questions) |

- With the reranker, both setups retrieve the same passages, so the embedding model can be chosen for cost, speed or privacy. On its own, `nomic-embed-text` ranked slightly better here; the chunking benchmark shows the same pattern (Evidence@3 0.789 vs 0.741 for vector search, 0.878 for both after reranking).
- The lower keyword recall of the cloud setup comes from paraphrasing, not from wrong answers. Llama 3 tends to quote the document ("probability", "in a safe manner"), while GPT-6 Luna rewords it ("likelihood", "safely"). Reading the six answers that scored differently shows all of them correct. Keyword recall cannot compare models with different writing styles; see [LLM judge](#llm-judge).
- The cost comes from the OpenAI usage page: 6,241 chat tokens for the 22 questions, reasoning tokens included, which stays under $0.0002 per question even if every token is billed at the output rate.

Reports: [local](evaluation/results/providers/ollama/report.md), [cloud](evaluation/results/providers/openai/report.md), [chunking benchmark with OpenAI embeddings](evaluation/results/chunking_benchmark/openai-embeddings/report.md). To reproduce, pass the providers to the evaluation:

```bash
docker compose exec -e LLM_PROVIDER=openai -e EMBED_PROVIDER=openai api python -m evaluation --generate --output evaluation/results/providers/openai
```

## Evaluation

The `evaluation/` package measures retrieval and answer quality against a labelled question set, so changes to chunking, retrieval, or prompts can be compared with numbers instead of impressions.

The bundled dataset, [`evaluation/datasets/nist_ai_rmf.jsonl`](evaluation/datasets/nist_ai_rmf.jsonl), contains 22 questions about the NIST AI RMF 1.0 document: 20 answerable questions labelled with their relevant pages and expected answer keywords, and 2 questions the document cannot answer.

A second dataset, [`chunking_benchmark.jsonl`](evaluation/datasets/chunking_benchmark.jsonl), adds the NIST CSF 2.0 and an FOMC press conference transcript and labels each answer with evidence sentences, so chunking changes can be measured. See the [dataset README](evaluation/datasets/README.md) and [Chunking](#chunking).

The harness runs each question through four retrieval strategies, built from the same components the API uses:

| Strategy | Description |
|---|---|
| `vector` | ChromaDB vector search only |
| `bm25` | BM25 keyword search only |
| `hybrid_rrf` | Vector + BM25 combined with Reciprocal Rank Fusion |
| `hybrid_rrf_rerank` | Hybrid retrieval followed by cross-encoder reranking (the production setup) |

### Metrics

- **Hit@k:** whether any of the top-k chunks comes from a relevant page
- **Recall@k:** share of the relevant pages covered by the top-k chunks
- **MRR:** mean reciprocal rank of the first relevant chunk
- **Evidence@k:** share of the labelled evidence sentences found in the top-k chunks (chunking benchmark only); reported with the characters the top-k chunks send to the model
- **Keyword recall:** share of expected keywords present in the generated answer (a lexical proxy, not a judge of correctness)
- **Citation rate / invalid citations:** share of answered questions whose answer cites at least one of the provided passages, and the number of answers citing a passage number that was not provided
- **LLM judge (optional):** a second model answers three YES/NO questions per answer: is it correct according to the labelled evidence, is every statement supported by the passages, and does every citation point to a passage that supports its statement. Rates are over the answered, answerable questions the judge decided on
- **Answer rate / abstention rate:** whether the model answers answerable questions and declines unanswerable ones

### Running the evaluation

Upload `nist.ai.100-1.pdf` through `POST /upload`, then run:

```bash
# Retrieval metrics only
docker compose exec api python -m evaluation

# Retrieval metrics and generated-answer scoring
docker compose exec api python -m evaluation --generate

# ...and LLM-judge scoring of the answers (needs OPENAI_API_KEY)
docker compose exec api python -m evaluation --generate --judge

# Check the judge against hand-labelled cases
docker compose exec api python -m evaluation.judge_check
```

The judge model is set with `JUDGE_PROVIDER` and `JUDGE_MODEL` (default `openai` / `gpt-6.1-sol`).

Reports are written to `evaluation/results/report.md` and `evaluation/results/report.json`. Use `--dataset` to evaluate another labelled JSONL file and `--ks` to change the cut-offs.

### Baseline results

Measured locally with `nomic-embed-text`, `cross-encoder/ms-marco-MiniLM-L-6-v2`, and `llama3` on the NIST AI RMF document (20 answerable questions). See the [full report](evaluation/results/report.md) for per-question results and generated answers.

| Strategy | Hit@1 | Hit@3 | Recall@5 | MRR@5 |
|---|---|---|---|---|
| `vector` | 0.950 | 0.950 | 0.925 | 0.950 |
| `bm25` | 0.750 | 0.900 | 0.900 | 0.825 |
| `hybrid_rrf` | 0.850 | 0.900 | 0.975 | 0.900 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 0.975 | 1.000 |

Answer generation with `hybrid_rrf_rerank` and the top 3 chunks: keyword recall 0.950, answer rate 1.000, abstention rate on unanswerable questions 1.000.

Observations:

- RRF fusion widens coverage (the best Recall@5 among the first-stage strategies) but places weaker BM25 matches near the top; the cross-encoder restores top-rank precision.
- The full pipeline is the only strategy that ranks a relevant chunk first for every question. Vector search alone misses `q11`, which depends on the exact term "cross-cutting".
- Reranking adds roughly 0.7 seconds per query on CPU in this setup.

The dataset is small and labelled by hand, so these numbers are a regression baseline for this project, not a general benchmark.

### Fixing a retrieval miss with the evaluation

The first evaluation run exposed one consistent miss: for `q11` ("Which AI RMF function is described as cross-cutting?") the GOVERN passage never reached the top 5, so the model answered that it did not know. Tracing each stage showed two causes:

1. **BM25 tokenization.** Text was split on whitespace only, so the query token `cross-cutting?` never matched `cross-cutting` in the document, and function words such as "which", "is", and "as" dominated the scores. The tokenizer now extracts word tokens (keeping hyphenated terms) and drops common stopwords, which moved the passage from rank 18 to rank 6 in BM25.
2. **Reranker.** `BAAI/bge-reranker-base` scored an unrelated "cross-sectoral profiles" chunk above the GOVERN passage. `cross-encoder/ms-marco-MiniLM-L-6-v2` ranks the GOVERN passage first.

| Change | BM25 MRR | Hybrid RRF MRR | Full pipeline MRR | Rerank latency |
|---|---|---|---|---|
| Initial | 0.785 | 0.873 | 0.950 | ~2.2 s |
| + BM25 tokenizer | 0.825 | 0.900 | 0.950 | ~2.0 s |
| + MiniLM reranker | 0.825 | 0.900 | **1.000** | **~0.7 s** |

### Citations

Answers cite the passages they rely on. Measured on the NIST AI RMF question set with the default settings, before and after adding citations to the prompt ([reports](evaluation/results/citations)):

| | Local (`llama3`) before → after | Cloud (`gpt-6-luna`) before → after |
|---|---|---|
| Citation rate | 0.00 → **1.00** | 0.00 → **1.00** |
| Answers with invalid citations | 0 → 0 | 0 → 0 |
| Keyword recall | 0.975 → 0.975 | 0.883 → 0.917 |
| Mean generation time | 19.7 s → 27.3 s | 1.7 s → 1.6 s |

Both models cite a provided passage in every answer and never cite one that does not exist, and answer quality is unchanged. Llama 3 writes about 45% longer answers when citing, which makes it slower, and sometimes adds stray citation markers or cites passages when it declines to answer. The citation rate only checks that a cited passage exists, not that it supports the statement; that is what the [LLM judge](#llm-judge) checks.

### LLM judge

Keyword recall rewards copying the document's wording, and the citation rate only checks that a cited passage exists. An LLM judge (`gpt-6.1-sol`) grades meaning instead. Before trusting it, it was checked against 13 hand-labelled cases ([`judge_cases.jsonl`](evaluation/datasets/judge_cases.jsonl)), including wrong numbers, incomplete answers, unsupported additions and mixed citations: it agreed on all 13 ([result](evaluation/results/judge/judge_check.md)).

Measured on the chunking benchmark (52 questions, three documents) with the default settings ([reports](evaluation/results/judge)):

| | Local (`llama3`) | Cloud (`gpt-6-luna`) |
|---|---|---|
| Judged correct | 0.80 | **0.94** |
| Grounded in the passages | 0.84 | **1.00** |
| Citations support their statements | 0.71 | **1.00** |
| Keyword recall | **0.845** | 0.775 |
| Mean generation time | 28.6 s | 1.7 s |

The judge reverses the keyword ranking: Llama 3 quotes more of the document but is wrong more often, and it often places all citations at the end of the answer or cites passages that do not support the statement. GPT-6 Luna paraphrases, which costs it keywords, not correctness. The local run was split into two parts to fit in memory, so its rates combine both reports.

Caveats: the judge is a model and can be wrong, 13 checked cases is a small sample, and the judge and the cloud generator come from the same provider, which may favour the cloud answers. Read the per-answer decisions in the reports rather than the rates alone.

## Chunking

The original chunker started a new chunk when the cosine similarity between consecutive sentences fell below 0.88. Measuring it on the NIST AI RMF showed that 97% of sentence boundaries were below that threshold, so chunks were in fact cut at the first sentence boundary after 300 characters. The project now offers two explicit strategies:

- **`sentence`** (default): packs the whole sentences of each section into chunks of roughly 300 to 1000 characters.
- **`semantic`**: embeds each sentence with its neighbours and splits where the distance between consecutive windows is above a percentile of all distances in the document, so the threshold adapts to the document and the embedding model. Short segments are merged and long ones are split into balanced parts.

Both were measured on the chunking benchmark with the full retrieval pipeline. Because larger chunks raise recall simply by sending more text, the comparison holds the context size fixed:

| Evidence found within | 1200 chars | 2000 chars | 3000 chars |
|---|---|---|---|
| `sentence` | **0.854** | **0.896** | **0.921** |
| `semantic` (90th percentile) | 0.781 | 0.854 | 0.900 |

Sentence-aligned chunks retrieve more evidence at every budget. In documents with clear headings, Docling's sections already follow topic boundaries; semantic splitting mostly makes chunks larger, and their embeddings less specific. Only in the FOMC transcript, which has no headings, is the semantic chunker slightly ahead, on 14 questions. `sentence` therefore stays the default. See the [full comparison](evaluation/results/chunking_benchmark/comparison.md) for all variants, results by document, and limitations.

### Document titles in chunks

Retrieval only sees a chunk's text. A chunk from the NIST CSF 2.0 starts with a section heading such as "3.1. CSF Profiles" but never says which framework it belongs to, so questions about the "Cybersecurity Framework" could not match it, and the AI RMF's similar "Target Profile" passage competed with it. With `CHUNK_CONTEXT=true` (the default), every chunk starts with its document title, taken from the document's first heading:

```text
The NIST Cybersecurity Framework (CSF) 2.0
3.1. CSF Profiles

A Target Profile specifies the desired outcomes...
```

Measured on the chunking benchmark with the full pipeline:

| | MRR | Hit@1 | Evidence@3 | Evidence at 1,600 chars | CSF Evidence@3 |
|---|---|---|---|---|---|
| Section heading only | 0.970 | 0.958 | 0.878 | 0.878 | 0.743 |
| Document title + section heading | **1.000** | **1.000** | **0.909** | **0.930** | **0.850** |

All gains come from the CSF, the document that shares vocabulary with the AI RMF; no question got worse. The AI RMF stays at 1.000 and the FOMC transcript is unchanged, since its only heading already is its title. The titles make chunks about 8% longer, and below about 1,000 characters of context they cost a little evidence; vector search alone also loses slightly on the AI RMF, which the reranker recovers. Upload documents again after upgrading: each chunking configuration has its own collection ([report](evaluation/results/chunking_benchmark/sentence-ctx/report.md)).

## Running the Tests

The project includes automated tests for the API, document parsing, chunking, ingestion, retrieval, generation, vector storage, and the evaluation harness.

Run the test suite with:

```bash
docker compose run --rm test
```

**Verified locally:** 185 tests passed. The same suite runs on GitHub Actions for every pull request and every push to `main`.

The suite includes unit tests that isolate application components from external model calls. The real-service integration and end-to-end checks were also run separately against Ollama and a temporary ChromaDB collection.

## Project Structure

```text
enterprise-rag-assistant/
├── api.py
├── chunking.py
├── config.py
├── document_parser.py
├── generator.py
├── ingestion.py
├── models.py
├── pipeline.py
├── vector_store.py
├── providers/
│   ├── base.py
│   ├── factory.py
│   ├── ollama.py
│   └── openai.py
├── retrieval/
│   ├── vector_search.py
│   ├── keyword_search.py
│   ├── fusion.py
│   ├── reranker.py
│   └── retriever.py
├── evaluation/
│   ├── datasets/
│   │   ├── README.md
│   │   ├── nist_ai_rmf.jsonl
│   │   └── chunking_benchmark.jsonl
│   ├── results/
│   │   └── chunking_benchmark/
│   ├── dataset.py
│   ├── metrics.py
│   ├── strategies.py
│   ├── evaluator.py
│   ├── report.py
│   └── __main__.py
├── ui/
│   ├── app.py
│   └── client.py
├── docs/
│   └── ui.png
├── tests/
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── Dockerfile.test
├── Dockerfile.ui
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── requirements-ui.txt
└── README.md
```

## Design Decisions

**Hybrid retrieval:** Vector search supports semantic matching, while BM25 adds lexical matching. RRF combines both ranked lists before reranking.

**Reranking:** A cross-encoder performs a second-stage relevance ranking on the candidate chunks.

**Source metadata:** Keeping page and heading information with each chunk allows the API to return inspectable source details.

**Local or cloud inference:** Ollama keeps documents on the machine; OpenAI answers about ten times faster. Both use the same retrieval pipeline, so the choice is a configuration change.

**Containerized setup:** Docker Compose provides a repeatable way to run the API and Ollama services.

## Scope and Limitations

The current implementation focuses on question answering over text documents. It does not currently provide:

- User authentication or authorization
- Persistent conversation history: the web interface keeps the chat on screen only, and each question is answered on its own
- Production-scale deployment guarantees

Answers depend on document quality, retrieval relevance, and model behavior. Source metadata helps inspect the retrieved material but does not guarantee that every generated claim is correct.

## Future Directions

Potential extensions include a larger multi-document evaluation set, authentication, and monitoring.

For chunking, the measurements point to three next steps: using the semantic chunker only for documents without headings, splitting long lists that lack sentence punctuation (one CSF appendix list currently becomes a single 5,819-character chunk), and prefixing chunks with document context so that similar frameworks such as the AI RMF and CSF are told apart more reliably.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
