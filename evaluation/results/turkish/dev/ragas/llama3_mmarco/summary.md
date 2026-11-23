# RAGAS Evaluation

| Configuration | Retrieval | Faithfulness | Answer relevancy |
|---|---|---|---|
| `hybrid_rerank` | Vector + BM25, RRF, cross-encoder reranking | 0.863 | 0.584 |

### Run details

- **Date:** 2026-11-21 20:13 UTC
- **Dataset:** kvkk_tr_dev.jsonl (20 questions)
- **Chat model:** ollama/llama3
- **Chat model (Turkish questions):** ollama/llama3
- **Reranker (Turkish questions):** cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- **Judge model:** openai/gpt-6.1-sol
- **Judge embeddings:** ollama/nomic-embed-text
- **Retrieval embeddings:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Passages per answer:** 3
- **Candidates per retriever:** 12
- **Mean retrieval / generation time:** `hybrid_rerank` 2445 ms / 8.9 s

Scores range from 0 to 1, higher is better; the best value of each column is in bold. Per-question scores, answers and passages are in the JSON and CSV file of each configuration.
