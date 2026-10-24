# RAG Evaluation Report

- **Date:** 2026-10-24 14:54 UTC
- **Dataset:** nist_ai_rmf.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** ollama/llama3
- **Candidates per retriever:** 12
- **Questions:** 22 (20 answerable, 2 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.900 | 0.900 | 0.900 | 0.850 | 0.875 | 0.875 | 0.900 | 14 |
| `bm25` | 0.800 | 0.900 | 0.900 | 0.700 | 0.850 | 0.900 | 0.850 | 1 |
| `hybrid_rrf` | 0.850 | 1.000 | 1.000 | 0.775 | 0.925 | 0.975 | 0.925 | 10 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.900 | 0.975 | 1.000 | 1.000 | 883 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.975 |
| Answer rate (answerable) | 0.950 |
| Abstention rate (unanswerable) | 1.000 |
| Citation rate (answered questions) | 0.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 19747 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| q01 | 0.000 | 1.000 | 0.500 | 1.000 |
| q02 | 1.000 | 0.000 | 0.500 | 1.000 |
| q03 | 1.000 | 1.000 | 1.000 | 1.000 |
| q04 | 1.000 | 0.000 | 0.500 | 1.000 |
| q05 | 1.000 | 1.000 | 1.000 | 1.000 |
| q06 | 1.000 | 1.000 | 1.000 | 1.000 |
| q07 | 1.000 | 1.000 | 1.000 | 1.000 |
| q08 | 1.000 | 1.000 | 1.000 | 1.000 |
| q09 | 1.000 | 1.000 | 1.000 | 1.000 |
| q10 | 1.000 | 1.000 | 1.000 | 1.000 |
| q11 | 0.000 | 1.000 | 1.000 | 1.000 |
| q12 | 1.000 | 1.000 | 1.000 | 1.000 |
| q13 | 1.000 | 1.000 | 1.000 | 1.000 |
| q14 | 1.000 | 1.000 | 1.000 | 1.000 |
| q15 | 1.000 | 0.500 | 1.000 | 1.000 |
| q16 | 1.000 | 1.000 | 1.000 | 1.000 |
| q17 | 1.000 | 1.000 | 1.000 | 1.000 |
| q18 | 1.000 | 0.500 | 1.000 | 1.000 |
| q19 | 1.000 | 1.000 | 1.000 | 1.000 |
| q20 | 1.000 | 1.000 | 1.000 | 1.000 |

## Generated Answers

**q01. What are the four core functions of the NIST AI Risk Management Framework?** _(keyword recall 1.000, abstained)_

> I don't know. The provided context only mentions the Artificial Intelligence Risk Management Framework (AI RMF 1.0), which has four core functions: GOVERN, MAP, MEASURE, and MANAGE. There is no mention of a NIST AI Risk Management Framework.

**q02. How does the AI RMF define risk?** _(keyword recall 1.000, answered)_

> According to the provided context, the AI RMF defines risk as "the composite measure of an event's probability of occurring and the magnitude or degree of the consequences of the corresponding event."

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered)_

> According to the provided context, the characteristics of trustworthy AI systems include:
>
> 1. Valid and reliable
> 2. Safe
> 3. Secure and resilient
> 4. Accountable and transparent
> 5. Explainable and interpretable
> 6. Privacy-enhanced
> 7. Fair with harmful bias managed

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered)_

> According to the provided context, validation in the context of AI systems is defined as "the 'confirmation, through the provision of objective evidence, that the requirements for a specific intended use or application have been fulfilled'" (Source: ISO 9000:2015).

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered)_

> According to the context, reliability is defined as "the ability of an item to perform as required, without failure, for a given time interval, under given conditions" (Source: ISO/IEC TS 5723:2022).

**q06. What are common security concerns for AI systems?** _(keyword recall 1.000, answered)_

> Common security concerns relate to adversarial examples, data poisoning, and the exfiltration of models, training data, or other intellectual property through AI system endpoints.

**q07. What is the difference between explainability and interpretability?** _(keyword recall 1.000, answered)_

> Explainability refers to a representation of the mechanisms underlying AI systems' operation (i.e., "how" a decision was made). Interpretability, on the other hand, answers the question of "why" a decision was made by the system and its meaning or context to the user.

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered)_

> The three major categories of AI bias identified by NIST are:
>
> 1. Systemic
> 2. Computational and statistical
> 3. Human-cognitive

**q09. What does risk tolerance refer to?** _(keyword recall 1.000, answered)_

> According to the provided context, risk tolerance refers to "the organization's or AI actor's readiness to bear the risk in order to achieve its objectives."

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 1.000, answered)_

> According to the context, when an AI system presents unacceptable negative risk levels, "development and deployment should cease in a safe manner until risks can be sufficiently managed."

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered)_

> GOVERN

**q12. What is the purpose of the MAP function?** _(keyword recall 0.500, answered)_

> The purpose of the MAP function is to enhance an organization's ability to identify risks and broader contributing factors, enabling negative risk prevention and informing decisions for processes such as model management, as well as an initial decision about appropriateness or the need for an AI solution.

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered)_

> The MEASURE function employs quantitative, qualitative, or mixed-method tools, techniques, and methodologies to analyze, assess, benchmark, and monitor AI risk and related impacts.

**q14. What does the MANAGE function entail?** _(keyword recall 1.000, answered)_

> The MANAGE function entails allocating risk resources to mapped and measured risks on a regular basis and as defined by the GOVERN function.

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered)_

> A Target Profile in the AI RMF indicates the outcomes needed to achieve the desired or target AI risk management goals.

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered)_

> TEVV stands for Test, Evaluation, Verification, and Validation. According to the provided context, TEVV tasks are performed throughout the AI lifecycle, which includes development, deployment, design, planning, and data phases.

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered)_

> The AI RMF will employ a two-number versioning system to track and identify major and minor changes. The first number will represent the generation of the AI RMF and its companion documents, and will change only with major revisions. Minor revisions will be tracked using '.n' after the generation number (e.g., 1.1).

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered)_

> According to the provided context, the Organisation for Economic Co-operation and Development (OECD) defines AI actors as "those who play an active role in the AI system lifecycle, including organizations and individuals that deploy or operate AI".

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered)_

> According to the provided context, pre-trained models can increase AI-specific risks in the following ways:
>
> 1. They can advance research and improve performance, but also increase levels of statistical uncertainty.
> 2. This can cause issues with bias management, scientific validity, and reproducibility.
>
> These are unique risks associated with AI systems that differ from traditional software risks.

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 1.000, answered)_

> According to the provided context, inscrutability in AI systems can be caused by:
>
> * Opaque nature of AI systems (limited explainability or interpretability)
> * Lack of transparency or documentation in AI system development or deployment
> * Inherent uncertainties in AI systems
>
> Inscrutability matters for risk measurement because it can complicate the process.

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, abstained)_

> I don't know. The provided context does not mention any specific allocation of funding for the development of the AI RMF.

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> I don't know. The provided context is about the NIST Cybersecurity Framework (CSF) 2.0, which has nothing to do with programming languages or machine learning models.
