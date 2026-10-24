# RAG Evaluation Report

- **Date:** 2026-10-24 15:10 UTC
- **Dataset:** nist_ai_rmf.jsonl
- **Embedding model:** openai/text-embedding-3-small
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** openai/gpt-6-luna
- **Candidates per retriever:** 12
- **Questions:** 22 (20 answerable, 2 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.900 | 0.950 | 0.950 | 0.825 | 0.875 | 0.925 | 0.925 | 43 |
| `bm25` | 0.800 | 0.900 | 0.900 | 0.700 | 0.850 | 0.900 | 0.850 | 2 |
| `hybrid_rrf` | 0.950 | 1.000 | 1.000 | 0.850 | 0.950 | 0.975 | 0.975 | 16 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.900 | 0.975 | 1.000 | 1.000 | 1390 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.917 |
| Answer rate (answerable) | 1.000 |
| Abstention rate (unanswerable) | 1.000 |
| Citation rate (answered questions) | 1.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 1580 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| q01 | 1.000 | 1.000 | 1.000 | 1.000 |
| q02 | 1.000 | 0.000 | 0.500 | 1.000 |
| q03 | 1.000 | 1.000 | 1.000 | 1.000 |
| q04 | 1.000 | 0.000 | 1.000 | 1.000 |
| q05 | 1.000 | 1.000 | 1.000 | 1.000 |
| q06 | 0.500 | 1.000 | 1.000 | 1.000 |
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

**q01. What are the four core functions of the NIST AI Risk Management Framework?** _(keyword recall 1.000, answered)_

> The four core functions are GOVERN, MAP, MEASURE, and MANAGE. [1][2]

**q02. How does the AI RMF define risk?** _(keyword recall 1.000, answered)_

> The AI RMF defines risk as the combined measure of the probability that an event occurs and the magnitude or degree of its consequences. [1]

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered)_

> Trustworthy AI systems should be valid and reliable; safe; secure and resilient; accountable and transparent; explainable and interpretable; privacy-enhanced; and fair, with harmful bias managed. [1]

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered)_

> Validation is the confirmation, through objective evidence, that requirements for a specific intended use or application have been fulfilled. [1]

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered)_

> Reliability is “the ability of an item to perform as required, without failure, for a given time interval, under given conditions.” [1]

**q06. What are common security concerns for AI systems?** _(keyword recall 1.000, answered)_

> Common security concerns include adversarial examples, data poisoning, and exfiltration of models, training data, or other intellectual property through AI system endpoints. [1] Security risks can also involve confidentiality, integrity, and availability, as well as attacks such as evasion, model extraction, and membership inference. [2][3]

**q07. What is the difference between explainability and interpretability?** _(keyword recall 0.000, answered)_

> Explainability describes how an AI system made a decision; interpretability explains why it made that decision and what the decision means in context. [1][2]

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered)_

> The three major categories are systemic bias, computational and statistical bias, and human-cognitive bias. [1]

**q09. What does risk tolerance refer to?** _(keyword recall 0.667, answered)_

> Risk tolerance refers to an organization’s or AI actor’s readiness to bear risk in order to achieve its objectives. [1]

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 1.000, answered)_

> Development and deployment should cease in a safe manner until the risks can be sufficiently managed. [1]

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered)_

> The GOVERN function is described as cross-cutting. [2]

**q12. What is the purpose of the MAP function?** _(keyword recall 1.000, answered)_

> The MAP function establishes the context for framing AI-system risks and helps organizations identify risks and contributing factors. Its findings support risk prevention, decisions about whether an AI solution is appropriate, and the MEASURE and MANAGE functions. [1][2][3]

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered)_

> The MEASURE function uses quantitative, qualitative, or mixed-method approaches to analyze, assess, benchmark, and monitor AI risks and related impacts. It documents system functionality and trustworthiness, tracks relevant metrics, and supports rigorous testing, performance assessment, uncertainty measurement, benchmarking, and reporting. Its results inform the MANAGE function’s risk monitoring and response efforts. [1][2][3]

**q14. What does the MANAGE function entail?** _(keyword recall 1.000, answered)_

> The MANAGE function entails regularly allocating risk resources to mapped and measured risks, as defined by GOVERN, and treating risks through plans to respond to, recover from, and communicate about incidents or events. [1]

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered)_

> A Target Profile describes the outcomes needed to achieve desired AI risk management goals. [1]

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered)_

> TEVV stands for Test, Evaluation, Verification, and Validation. [1] TEVV tasks are performed throughout the AI lifecycle. [1]

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered)_

> The AI RMF uses a two-number versioning system: the first number identifies the generation and changes only with major revisions; minor revisions are indicated by “.n” after it (for example, 1.1). [1]

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered)_

> The OECD defines AI actors as those who play an active role in the AI system lifecycle, including organizations and individuals who deploy or operate AI. [1]

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered)_

> Pre-trained models can increase statistical uncertainty and create challenges for bias management, scientific validity, and reproducibility. Their emergent properties can also make failure modes harder to predict. [2]

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 0.667, answered)_

> Inscrutability can result from limited explainability or interpretability, a lack of transparency or documentation in development or deployment, or inherent uncertainties in AI systems. It matters because inscrutable systems can make risk measurement more difficult. [1]

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, abstained)_

> I don’t know. The provided context does not state how much funding NIST allocated to develop the AI RMF. [1][3]

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> The provided context does not say which programming language NIST recommends for building machine learning models.
