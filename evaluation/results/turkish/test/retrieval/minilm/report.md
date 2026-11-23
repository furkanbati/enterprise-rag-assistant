# RAG Evaluation Report

- **Date:** 2026-11-22 14:45 UTC
- **Dataset:** kvkk_tr_test.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Reranker (Turkish questions):** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** not evaluated
- **Judge model:** not used
- **Candidates per retriever:** 12
- **Questions:** 12 (10 answerable, 2 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.500 | 0.700 | 0.700 | 0.450 | 0.650 | 0.700 | 0.583 | 22 |
| `bm25` | 0.700 | 0.900 | 0.900 | 0.650 | 0.900 | 0.900 | 0.783 | 1 |
| `hybrid_rrf` | 0.600 | 0.600 | 0.900 | 0.550 | 0.550 | 0.850 | 0.665 | 25 |
| `hybrid_rrf_rerank` | 0.600 | 0.700 | 0.800 | 0.550 | 0.700 | 0.800 | 0.675 | 2221 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.250 | 0.400 | 0.500 | 365 | 1005 | 1813 |
| `bm25` | 0.600 | 0.900 | 0.900 | 416 | 1600 | 2440 |
| `hybrid_rrf` | 0.500 | 0.500 | 0.750 | 375 | 1139 | 1938 |
| `hybrid_rrf_rerank` | 0.500 | 0.700 | 0.800 | 395 | 1586 | 2488 |

### Evidence@5 by Source

| Strategy | kvkk_6698.pdf |
| --- | --- |
| `vector` | 0.500 |
| `bm25` | 0.900 |
| `hybrid_rrf` | 0.750 |
| `hybrid_rrf_rerank` | 0.800 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| t21 | 0.000 | 0.500 | 0.250 | 0.250 |
| t22 | 0.000 | 0.333 | 0.200 | 0.500 |
| t23 | 1.000 | 1.000 | 1.000 | 1.000 |
| t24 | 0.000 | 1.000 | 0.200 | 0.000 |
| t25 | 0.333 | 0.000 | 0.000 | 0.000 |
| t26 | 1.000 | 1.000 | 1.000 | 1.000 |
| t27 | 1.000 | 1.000 | 1.000 | 1.000 |
| t28 | 1.000 | 1.000 | 1.000 | 1.000 |
| t29 | 1.000 | 1.000 | 1.000 | 1.000 |
| t32 | 0.500 | 1.000 | 1.000 | 1.000 |
