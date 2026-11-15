# RAGAS Evaluation

| Configuration | Retrieval | Faithfulness | Answer relevancy | Context precision | Context recall |
|---|---|---|---|---|---|
| `vector` | Vector search only | 0.948 | 0.704 | 0.727 | 0.745 |
| `hybrid` | Vector + BM25, Reciprocal Rank Fusion | 0.954 | 0.783 | 0.776 | **0.900** |
| `hybrid_rerank` | Vector + BM25, RRF, cross-encoder reranking | **0.966** | **0.789** | **0.828** | 0.848 |

### By language

| Configuration | Language | Faithfulness | Answer relevancy | Context precision | Context recall |
|---|---|---|---|---|---|
| `vector` | English | 0.976 | 0.801 | 0.901 | 0.881 |
| `vector` | Turkish | 0.875 | 0.451 | 0.271 | 0.388 |
| `hybrid` | English | 1.000 | 0.866 | 0.857 | 1.000 |
| `hybrid` | Turkish | 0.833 | 0.565 | 0.562 | 0.637 |
| `hybrid_rerank` | English | 1.000 | 0.872 | 0.952 | 0.952 |
| `hybrid_rerank` | Turkish | 0.875 | 0.571 | 0.500 | 0.575 |

### Run details

- **Date:** 2026-11-14 10:14 UTC
- **Dataset:** ragas_testset.jsonl (29 questions)
- **Chat model:** openai/gpt-6-luna
- **Judge model:** openai/gpt-6.1-sol
- **Judge embeddings:** ollama/nomic-embed-text
- **Retrieval embeddings:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Passages per answer:** 3
- **Candidates per retriever:** 12
- **Mean retrieval / generation time:** `vector` 1191 ms / 1.5 s, `hybrid` 1270 ms / 1.4 s, `hybrid_rerank` 2455 ms / 1.4 s

Scores range from 0 to 1, higher is better; the best value of each column is in bold. Per-question scores, answers and passages are in the JSON and CSV file of each configuration.
