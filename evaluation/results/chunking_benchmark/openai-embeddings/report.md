# RAG Evaluation Report

- **Date:** 2026-10-22 04:33 UTC
- **Dataset:** chunking_benchmark.jsonl
- **Embedding model:** openai/text-embedding-3-small
- **Chunking:** sentence
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** not evaluated
- **Candidates per retriever:** 12
- **Questions:** 52 (48 answerable, 4 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.833 | 0.938 | 0.958 | 0.740 | 0.896 | 0.938 | 0.884 | 26 |
| `bm25` | 0.854 | 0.938 | 0.938 | 0.750 | 0.854 | 0.885 | 0.896 | 1 |
| `hybrid_rrf` | 0.917 | 0.938 | 0.979 | 0.802 | 0.854 | 0.927 | 0.936 | 25 |
| `hybrid_rrf_rerank` | 0.958 | 0.979 | 1.000 | 0.833 | 0.927 | 0.958 | 0.970 | 764 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.494 | 0.741 | 0.802 | 387 | 1205 | 2276 |
| `bm25` | 0.556 | 0.747 | 0.778 | 391 | 1202 | 2006 |
| `hybrid_rrf` | 0.577 | 0.789 | 0.876 | 400 | 1177 | 2126 |
| `hybrid_rrf_rerank` | 0.680 | 0.878 | 0.896 | 401 | 1246 | 2081 |

### Evidence@5 by Source

| Strategy | nist.ai.100-1.pdf | NIST.CSWP.29.pdf | FOMCpresconf20240918.pdf |
| --- | --- | --- | --- |
| `vector` | 0.900 | 0.721 | 0.744 |
| `bm25` | 0.800 | 0.686 | 0.839 |
| `hybrid_rrf` | 0.950 | 0.771 | 0.875 |
| `hybrid_rrf_rerank` | 1.000 | 0.805 | 0.839 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| q01 | 0.333 | 1.000 | 1.000 | 1.000 |
| q02 | 0.500 | 0.000 | 0.250 | 1.000 |
| q03 | 1.000 | 1.000 | 1.000 | 1.000 |
| q04 | 1.000 | 0.000 | 1.000 | 1.000 |
| q05 | 1.000 | 1.000 | 1.000 | 1.000 |
| q06 | 1.000 | 1.000 | 1.000 | 1.000 |
| q07 | 1.000 | 1.000 | 1.000 | 1.000 |
| q08 | 1.000 | 1.000 | 1.000 | 1.000 |
| q09 | 1.000 | 1.000 | 1.000 | 1.000 |
| q10 | 1.000 | 1.000 | 1.000 | 1.000 |
| q11 | 0.000 | 0.500 | 0.200 | 1.000 |
| q12 | 1.000 | 1.000 | 1.000 | 1.000 |
| q13 | 1.000 | 1.000 | 1.000 | 1.000 |
| q14 | 1.000 | 1.000 | 1.000 | 1.000 |
| q15 | 1.000 | 1.000 | 1.000 | 1.000 |
| q16 | 1.000 | 1.000 | 1.000 | 1.000 |
| q17 | 1.000 | 1.000 | 1.000 | 1.000 |
| q18 | 1.000 | 0.500 | 1.000 | 1.000 |
| q19 | 1.000 | 1.000 | 1.000 | 1.000 |
| q20 | 1.000 | 1.000 | 1.000 | 1.000 |
| c01 | 0.250 | 0.500 | 0.500 | 0.333 |
| c02 | 1.000 | 1.000 | 1.000 | 1.000 |
| c03 | 1.000 | 1.000 | 1.000 | 1.000 |
| c04 | 1.000 | 1.000 | 1.000 | 1.000 |
| c05 | 1.000 | 1.000 | 1.000 | 1.000 |
| c06 | 1.000 | 1.000 | 1.000 | 1.000 |
| c07 | 1.000 | 1.000 | 1.000 | 1.000 |
| c08 | 1.000 | 1.000 | 1.000 | 1.000 |
| c09 | 1.000 | 1.000 | 1.000 | 1.000 |
| c10 | 0.500 | 1.000 | 1.000 | 1.000 |
| c11 | 0.500 | 1.000 | 1.000 | 1.000 |
| c12 | 0.000 | 0.000 | 0.000 | 0.250 |
| c13 | 0.333 | 1.000 | 1.000 | 1.000 |
| c14 | 1.000 | 0.500 | 1.000 | 1.000 |
| f01 | 1.000 | 1.000 | 1.000 | 1.000 |
| f02 | 1.000 | 1.000 | 1.000 | 1.000 |
| f03 | 1.000 | 1.000 | 1.000 | 1.000 |
| f04 | 1.000 | 1.000 | 1.000 | 1.000 |
| f05 | 1.000 | 1.000 | 1.000 | 1.000 |
| f06 | 1.000 | 1.000 | 1.000 | 1.000 |
| f07 | 1.000 | 1.000 | 1.000 | 1.000 |
| f08 | 1.000 | 1.000 | 1.000 | 1.000 |
| f09 | 1.000 | 1.000 | 1.000 | 1.000 |
| f10 | 1.000 | 1.000 | 1.000 | 1.000 |
| f11 | 1.000 | 1.000 | 1.000 | 1.000 |
| f12 | 1.000 | 1.000 | 1.000 | 1.000 |
| f13 | 1.000 | 1.000 | 1.000 | 1.000 |
| f14 | 1.000 | 1.000 | 1.000 | 1.000 |
