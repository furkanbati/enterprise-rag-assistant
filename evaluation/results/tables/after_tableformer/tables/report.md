# RAG Evaluation Report

- **Date:** 2026-11-24 07:13 UTC
- **Dataset:** nist_tables.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Reranker (Turkish questions):** cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
- **Chat model:** ollama/llama3
- **Judge model:** not used
- **Candidates per retriever:** 12
- **Questions:** 6 (6 answerable, 0 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.667 | 0.833 | 0.833 | 0.667 | 0.833 | 0.833 | 0.750 | 3 |
| `bm25` | 0.833 | 1.000 | 1.000 | 0.833 | 1.000 | 1.000 | 0.917 | 1 |
| `hybrid_rrf` | 0.833 | 1.000 | 1.000 | 0.833 | 1.000 | 1.000 | 0.917 | 3 |
| `hybrid_rrf_rerank` | 0.833 | 1.000 | 1.000 | 0.833 | 1.000 | 1.000 | 0.917 | 1484 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.333 | 0.333 | 0.333 | 397 | 1171 | 2042 |
| `bm25` | 0.333 | 0.500 | 0.500 | 416 | 1403 | 2383 |
| `hybrid_rrf` | 0.333 | 0.500 | 0.500 | 446 | 1266 | 2089 |
| `hybrid_rrf_rerank` | 0.333 | 0.500 | 0.500 | 434 | 1364 | 1980 |

### Evidence@5 by Source

| Strategy | nist.ai.100-1.pdf |
| --- | --- |
| `vector` | 0.333 |
| `bm25` | 0.500 |
| `hybrid_rrf` | 0.500 |
| `hybrid_rrf_rerank` | 0.500 |

## Missing Evidence

These evidence sentences were not found in any indexed chunk, which points to a labelling or parsing problem.

- `tb01`: Processes and procedures are in place for decommissioning and phasing out AI systems safely
- `tb02`: Executive leadership of the organization takes responsibility for decisions about risks associated with AI system
- `tb05`: Risk response options can include mitigating, transferring, avoiding, or accepting

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 1.000 |
| Answer rate (answerable) | 1.000 |
| Abstention rate (unanswerable) | n/a |
| Citation rate (answered questions) | 1.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 6395 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| tb01 | 0.500 | 1.000 | 1.000 | 1.000 |
| tb02 | 1.000 | 1.000 | 1.000 | 1.000 |
| tb03 | 0.000 | 1.000 | 0.500 | 1.000 |
| tb04 | 1.000 | 1.000 | 1.000 | 1.000 |
| tb05 | 1.000 | 1.000 | 1.000 | 1.000 |
| tb06 | 1.000 | 0.500 | 1.000 | 0.500 |

## Generated Answers

**tb01. Which GOVERN subcategory covers decommissioning and phasing out AI systems?** _(keyword recall 1.000, answered)_

> GOVERN 1.7: Processes and procedures are in place for decom- missioning and phasing out AI systems safely and in a man- ner that does not increase risks or decrease the organization's trustworthiness. [1][3]
>
> Answer: GOVERN 1.7

**tb02. According to GOVERN 2.3, who takes responsibility for decisions about risks associated with AI system development and deployment?** _(keyword recall 1.000, answered)_

> According to GOVERN 2.3, Executive leadership of the organization takes responsibility for decisions about risks associated with AI system development and deployment. [2]

**tb03. What does MAP 1.5 say about organizational risk tolerances?** _(keyword recall 1.000, answered)_

> According to the provided context [1], MAP 1.5 states: "Organizational risk tolerances are determined and documented."

**tb04. Which MEASURE subcategory addresses the environmental impact and sustainability of AI model training?** _(keyword recall 1.000, answered)_

> According to the provided context, MEASURE 2.12: Environmental impact and sustainability of AI model training and management activities, as identified in the MAP function, are assessed and documented. [1][3]
>
> Answer: MEASURE 2.12

**tb05. What risk response options does MANAGE 1.3 list for high-priority AI risks?** _(keyword recall 1.000, answered)_

> According to the provided context, MANAGE 1.3 lists the following risk response options for high-priority AI risks:
>
> * Mitigating
> * Transferring
> * Avoiding
> * Accepting
>
> [1]

**tb06. How does the AI RMF define negative residual risks?** _(keyword recall 1.000, answered)_

> According to the context, negative residual risks are defined as the sum of all unmitigated risks [2].
