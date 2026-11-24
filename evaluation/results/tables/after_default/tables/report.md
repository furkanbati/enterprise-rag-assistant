# RAG Evaluation Report

- **Date:** 2026-11-24 06:55 UTC
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
| `vector` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 |
| `bm25` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| `hybrid_rrf` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2 |
| `hybrid_rrf_rerank` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1226 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.000 | 0.000 | 0.000 | 493 | 1406 | 2321 |
| `bm25` | 0.000 | 0.000 | 0.000 | 410 | 1350 | 2343 |
| `hybrid_rrf` | 0.000 | 0.000 | 0.000 | 432 | 1346 | 2395 |
| `hybrid_rrf_rerank` | 0.000 | 0.000 | 0.000 | 432 | 1311 | 2454 |

### Evidence@5 by Source

| Strategy | nist.ai.100-1.pdf |
| --- | --- |
| `vector` | 0.000 |
| `bm25` | 0.000 |
| `hybrid_rrf` | 0.000 |
| `hybrid_rrf_rerank` | 0.000 |

## Missing Evidence

These evidence sentences were not found in any indexed chunk, which points to a labelling or parsing problem.

- `tb01`: Processes and procedures are in place for decommissioning and phasing out AI systems safely
- `tb02`: Executive leadership of the organization takes responsibility for decisions about risks associated with AI system
- `tb03`: Organizational risk tolerances are determined and documented
- `tb04`: Environmental impact and sustainability of AI model training and management activities
- `tb05`: Risk response options can include mitigating, transferring, avoiding, or accepting
- `tb06`: Negative residual risks (defined as the sum of all unmitigated risks)

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.000 |
| Answer rate (answerable) | 0.333 |
| Abstention rate (unanswerable) | n/a |
| Citation rate (answered questions) | 0.500 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 6052 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| tb01 | 0.000 | 0.000 | 0.000 | 0.000 |
| tb02 | 0.000 | 0.000 | 0.000 | 0.000 |
| tb03 | 0.000 | 0.000 | 0.000 | 0.000 |
| tb04 | 0.000 | 0.000 | 0.000 | 0.000 |
| tb05 | 0.000 | 0.000 | 0.000 | 0.000 |
| tb06 | 0.000 | 0.000 | 0.000 | 0.000 |

## Generated Answers

**tb01. Which GOVERN subcategory covers decommissioning and phasing out AI systems?** _(keyword recall 0.000, abstained)_

> I don't know.
>
> The context only provides information about the GOVERN function in general, but does not specify a subcategory related to decommissioning and phasing out AI systems.

**tb02. According to GOVERN 2.3, who takes responsibility for decisions about risks associated with AI system development and deployment?** _(keyword recall 0.000, answered)_

> According to the provided context, it is the joint responsibility of all AI actors to determine whether AI technology is an appropriate or necessary tool for a given context or purpose, and how to use it responsibly. This is stated in [2] page 17, section 3. AI Risks and Trustworthiness.
>
> This joint responsibility is emphasized as it is stated that "It is the joint responsibility of all AI actors" to determine the trustworthiness characteristics and the relative risks, impacts, costs, and benefits.

**tb03. What does MAP 1.5 say about organizational risk tolerances?** _(keyword recall 0.000, abstained)_

> I don't know.
>
> The context only provides information about MAP and governance, but it does not mention MAP 1.5 or organizational risk tolerances specifically.

**tb04. Which MEASURE subcategory addresses the environmental impact and sustainability of AI model training?** _(keyword recall 0.000, answered)_

> According to the provided context, there is no specific subcategory in the MEASURE function that addresses the environmental impact and sustainability of AI model training. The context only mentions social responsibility, sustainability, and AI risk measurements, but not environmental impact specifically.
>
> [Citing no specific passage number, as the information is not found in the provided context.]

**tb05. What risk response options does MANAGE 1.3 list for high-priority AI risks?** _(keyword recall 0.000, abstained)_

> The risk response options for high-priority AI risks are not mentioned in the provided context. The context only discusses risk prioritization and does not specify response options for high-priority risks. Therefore, I don't know.

**tb06. How does the AI RMF define negative residual risks?** _(keyword recall 0.000, abstained)_

> According to the provided context, negative residual risks are not explicitly defined. The context only mentions "potential negative impacts" [1] and "significant negative impacts" [3], but does not provide a formal definition of negative residual risks.
>
> However, it is mentioned that residual risk is defined as "risk remaining after risk treatment" [2], which is consistent with the ISO GUIDE 73 definition.
