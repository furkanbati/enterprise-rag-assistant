# RAGAS Evaluation

| Configuration | Retrieval | Faithfulness | Answer relevancy |
|---|---|---|---|
| `vector` | Vector search only | 0.831 | 0.706 |
| `hybrid` | Vector + BM25, Reciprocal Rank Fusion | **0.931** | 0.761 |
| `hybrid_rerank` | Vector + BM25, RRF, cross-encoder reranking | 0.887 | **0.836** |

### By language

| Configuration | Language | Faithfulness | Answer relevancy |
|---|---|---|---|
| `vector` | English | 0.883 | 0.829 |
| `vector` | Turkish | 0.696 | 0.385 |
| `hybrid` | English | 0.973 | 0.871 |
| `hybrid` | Turkish | 0.823 | 0.472 |
| `hybrid_rerank` | English | 0.934 | 0.939 |
| `hybrid_rerank` | Turkish | 0.766 | 0.565 |

### Run details

- **Date:** `vector` 2026-11-14 16:20 UTC, `hybrid` 2026-11-14 16:20 UTC, `hybrid_rerank` 2026-11-14 19:47 UTC
- **Dataset:** ragas_testset.jsonl (29 questions)
- **Chat model:** ollama/llama3
- **Judge model:** openai/gpt-6.1-sol
- **Judge embeddings:** ollama/nomic-embed-text
- **Retrieval embeddings:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Passages per answer:** 3
- **Candidates per retriever:** 12
- **Mean retrieval / generation time:** `vector` 976 ms / 81.2 s, `hybrid` 1026 ms / 71.7 s, `hybrid_rerank` 2024 ms / 79.7 s

Scores range from 0 to 1, higher is better; the best value of each column is in bold. Per-question scores, answers and passages are in the JSON and CSV file of each configuration.
