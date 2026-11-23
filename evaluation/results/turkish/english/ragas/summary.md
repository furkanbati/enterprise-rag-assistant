# RAGAS Evaluation

| Configuration | Retrieval | Faithfulness | Answer relevancy |
|---|---|---|---|
| `hybrid_rerank` | Vector + BM25, RRF, cross-encoder reranking | 0.977 | 0.953 |

### Run details

- **Date:** 2026-11-22 14:08 UTC
- **Dataset:** ragas_testset.jsonl (21 questions)
- **Chat model:** ollama/llama3
- **Chat model (Turkish questions):** ollama/qwen3.5:4b
- **Reranker (Turkish questions):** cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- **Judge model:** openai/gpt-6.1-sol
- **Judge embeddings:** ollama/nomic-embed-text
- **Retrieval embeddings:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Passages per answer:** 3
- **Candidates per retriever:** 12
- **Mean retrieval / generation time:** `hybrid_rerank` 1108 ms / 6.7 s

Scores range from 0 to 1, higher is better; the best value of each column is in bold. Per-question scores, answers and passages are in the JSON and CSV file of each configuration.
