# RAG Evaluation Report

- **Date:** 2026-10-24 14:55 UTC
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
| `vector` | 0.900 | 0.950 | 0.950 | 0.825 | 0.875 | 0.925 | 0.925 | 13 |
| `bm25` | 0.800 | 0.900 | 0.900 | 0.700 | 0.850 | 0.900 | 0.850 | 1 |
| `hybrid_rrf` | 0.950 | 1.000 | 1.000 | 0.850 | 0.950 | 0.975 | 0.975 | 13 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.900 | 0.975 | 1.000 | 1.000 | 1039 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.883 |
| Answer rate (answerable) | 1.000 |
| Abstention rate (unanswerable) | 0.500 |
| Citation rate (answered questions) | 0.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 1673 |

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

> The four core functions are **GOVERN, MAP, MEASURE, and MANAGE**.

**q02. How does the AI RMF define risk?** _(keyword recall 1.000, answered)_

> The AI RMF defines risk as the combined measure of the probability that an event will occur and the magnitude or degree of its consequences.

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered)_

> Trustworthy AI systems are **valid and reliable; safe; secure and resilient; accountable and transparent; explainable and interpretable; privacy-enhanced; and fair, with harmful bias managed.** These characteristics should be balanced according to the system’s context of use.

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered)_

> Validation is the confirmation, through objective evidence, that the requirements for a specific intended use or application have been fulfilled.

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered)_

> Reliability is the ability of an item to perform as required, without failure, for a given time interval and under given conditions.

**q06. What are common security concerns for AI systems?** _(keyword recall 1.000, answered)_

> Common security concerns include adversarial examples, data poisoning, and exfiltration of models, training data, or other intellectual property through AI system endpoints. Other concerns include evasion, model extraction, membership inference, availability, and attacks on the system’s confidentiality, integrity, or availability.

**q07. What is the difference between explainability and interpretability?** _(keyword recall 0.000, answered)_

> Explainability describes how an AI system works and how it made a decision. Interpretability describes why that decision was made and what the output means in the context of the system’s purpose.

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered)_

> Systemic bias, computational and statistical bias, and human-cognitive bias.

**q09. What does risk tolerance refer to?** _(keyword recall 0.667, answered)_

> Risk tolerance refers to an organization’s or AI actor’s readiness to bear risk in order to achieve its objectives.

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 1.000, answered)_

> Development and deployment should cease in a safe manner until the risks can be sufficiently managed.

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered)_

> GOVERN.

**q12. What is the purpose of the MAP function?** _(keyword recall 1.000, answered)_

> The MAP function establishes the context for identifying risks related to an AI system and broader contributing factors. Its outcomes help prevent negative risks, inform decisions about whether an AI solution is appropriate, and provide a basis for the MEASURE and MANAGE functions.

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered)_

> The MEASURE function uses quantitative, qualitative, or mixed-method approaches to assess, benchmark, and monitor AI risks and impacts. It documents system functionality and trustworthiness, tracks relevant metrics, and uses rigorous testing, performance assessment, uncertainty measures, benchmarks, and reporting to inform risk monitoring and response in the MANAGE function.

**q14. What does the MANAGE function entail?** _(keyword recall 0.667, answered)_

> The MANAGE function entails regularly allocating resources to mapped and measured risks, as defined by GOVERN, and planning how to respond to, recover from, and communicate about incidents or events. It also includes prioritizing risks, ongoing monitoring, and continual improvement as systems and circumstances evolve.

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered)_

> A Target Profile describes the outcomes needed to achieve an organization’s desired AI risk management goals. It represents the desired target state of specific AI risk management activities.

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered)_

> TEVV stands for Test, Evaluation, Verification, and Validation. These tasks are performed throughout the AI lifecycle, including during design and planning, development, and deployment.

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered)_

> The AI RMF will use a two-number versioning system: the first number tracks major revisions, and a “.n” after it tracks minor revisions (for example, 1.0 and 1.1).

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered)_

> The OECD defines AI actors as those who play an active role in the AI system lifecycle, including organizations and individuals that deploy or operate AI.

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered)_

> Pre-trained models can increase statistical uncertainty and create challenges with bias management, scientific validity, and reproducibility. Their emergent properties can also make failure modes harder to predict.

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 0.333, answered)_

> Inscrutability can result from AI systems’ opacity (limited explainability or interpretability), inadequate transparency or documentation during development or deployment, or inherent uncertainty. It makes risk harder to measure because the system’s risks or failures may not be well-defined or understood. Difficulty measuring a risk does not, by itself, mean the system is either high- or low-risk.

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, answered)_

> The provided context does not state how much funding NIST allocated to develop the AI RMF.

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> The provided context does not specify a programming language recommended by NIST for building machine learning models.
