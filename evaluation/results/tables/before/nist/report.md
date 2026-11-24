# RAG Evaluation Report

- **Date:** 2026-11-24 06:52 UTC
- **Dataset:** nist_ai_rmf.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Reranker (Turkish questions):** cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- **Chat model:** not evaluated
- **Judge model:** not used
- **Candidates per retriever:** 12
- **Questions:** 22 (20 answerable, 2 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.900 | 0.900 | 0.950 | 0.850 | 0.875 | 0.900 | 0.910 | 2 |
| `bm25` | 0.800 | 0.900 | 0.900 | 0.700 | 0.850 | 0.900 | 0.850 | 0 |
| `hybrid_rrf` | 0.850 | 1.000 | 1.000 | 0.775 | 0.925 | 0.950 | 0.908 | 2 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.900 | 0.975 | 1.000 | 1.000 | 984 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| q01 | 0.200 | 1.000 | 0.500 | 1.000 |
| q02 | 1.000 | 0.000 | 0.333 | 1.000 |
| q03 | 1.000 | 1.000 | 1.000 | 1.000 |
| q04 | 1.000 | 0.000 | 0.333 | 1.000 |
| q05 | 1.000 | 0.500 | 1.000 | 1.000 |
| q06 | 1.000 | 1.000 | 1.000 | 1.000 |
| q07 | 1.000 | 1.000 | 1.000 | 1.000 |
| q08 | 1.000 | 1.000 | 1.000 | 1.000 |
| q09 | 1.000 | 1.000 | 1.000 | 1.000 |
| q10 | 1.000 | 1.000 | 1.000 | 1.000 |
| q11 | 0.000 | 1.000 | 1.000 | 1.000 |
| q12 | 1.000 | 1.000 | 1.000 | 1.000 |
| q13 | 1.000 | 1.000 | 1.000 | 1.000 |
| q14 | 1.000 | 1.000 | 1.000 | 1.000 |
| q15 | 1.000 | 1.000 | 1.000 | 1.000 |
| q16 | 1.000 | 1.000 | 1.000 | 1.000 |
| q17 | 1.000 | 1.000 | 1.000 | 1.000 |
| q18 | 1.000 | 0.500 | 1.000 | 1.000 |
| q19 | 1.000 | 1.000 | 1.000 | 1.000 |
| q20 | 1.000 | 1.000 | 1.000 | 1.000 |
