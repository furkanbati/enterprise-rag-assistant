# RAG Evaluation Report

- **Date:** 2026-11-21 19:36 UTC
- **Dataset:** kvkk_tr_dev.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Reranker (Turkish questions):** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** not evaluated
- **Judge model:** not used
- **Candidates per retriever:** 12
- **Questions:** 20 (19 answerable, 1 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.579 | 0.737 | 0.789 | 0.553 | 0.684 | 0.737 | 0.660 | 15 |
| `bm25` | 0.789 | 0.895 | 1.000 | 0.737 | 0.868 | 0.974 | 0.857 | 2 |
| `hybrid_rrf` | 0.684 | 0.789 | 0.842 | 0.632 | 0.789 | 0.842 | 0.750 | 17 |
| `hybrid_rrf_rerank` | 0.737 | 0.789 | 0.895 | 0.684 | 0.789 | 0.895 | 0.778 | 1497 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.158 | 0.395 | 0.421 | 279 | 955 | 1699 |
| `bm25` | 0.500 | 0.658 | 0.763 | 472 | 1437 | 2370 |
| `hybrid_rrf` | 0.289 | 0.605 | 0.632 | 358 | 1052 | 1941 |
| `hybrid_rrf_rerank` | 0.421 | 0.658 | 0.763 | 412 | 1406 | 2407 |

### Evidence@5 by Source

| Strategy | kvkk_6698.pdf |
| --- | --- |
| `vector` | 0.421 |
| `bm25` | 0.763 |
| `hybrid_rrf` | 0.632 |
| `hybrid_rrf_rerank` | 0.763 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| t01 | 0.200 | 0.500 | 0.500 | 0.200 |
| t02 | 0.000 | 0.333 | 0.000 | 0.000 |
| t03 | 1.000 | 1.000 | 1.000 | 1.000 |
| t04 | 1.000 | 1.000 | 1.000 | 1.000 |
| t05 | 1.000 | 1.000 | 1.000 | 1.000 |
| t06 | 1.000 | 1.000 | 1.000 | 1.000 |
| t07 | 1.000 | 1.000 | 1.000 | 1.000 |
| t08 | 0.000 | 1.000 | 0.000 | 0.250 |
| t09 | 0.000 | 0.250 | 0.000 | 0.333 |
| t10 | 0.000 | 1.000 | 0.250 | 1.000 |
| t11 | 1.000 | 0.200 | 1.000 | 0.000 |
| t12 | 1.000 | 1.000 | 1.000 | 1.000 |
| t13 | 0.333 | 1.000 | 1.000 | 1.000 |
| t14 | 1.000 | 1.000 | 1.000 | 1.000 |
| t15 | 1.000 | 1.000 | 1.000 | 1.000 |
| t17 | 0.500 | 1.000 | 1.000 | 1.000 |
| t18 | 1.000 | 1.000 | 1.000 | 1.000 |
| t19 | 1.000 | 1.000 | 1.000 | 1.000 |
| t20 | 0.500 | 1.000 | 0.500 | 1.000 |
