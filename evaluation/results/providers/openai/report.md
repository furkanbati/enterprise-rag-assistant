# RAG Evaluation Report

- **Date:** 2026-10-22 04:32 UTC
- **Dataset:** nist_ai_rmf.jsonl
- **Embedding model:** openai/text-embedding-3-small
- **Chunking:** sentence
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** openai/gpt-6-luna
- **Candidates per retriever:** 12
- **Questions:** 22 (20 answerable, 2 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.850 | 0.950 | 0.950 | 0.800 | 0.900 | 0.925 | 0.892 | 28 |
| `bm25` | 0.800 | 0.900 | 0.900 | 0.725 | 0.850 | 0.900 | 0.850 | 1 |
| `hybrid_rrf` | 0.900 | 0.900 | 1.000 | 0.825 | 0.875 | 0.975 | 0.922 | 28 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.900 | 0.975 | 0.975 | 1.000 | 856 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.875 |
| Answer rate (answerable) | 1.000 |
| Abstention rate (unanswerable) | 1.000 |
| Mean generation latency (ms) | 1285 |

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

## Generated Answers

**q01. What are the four core functions of the NIST AI Risk Management Framework?** _(keyword recall 1.000, answered)_

> GOVERN, MAP, MEASURE, and MANAGE.

**q02. How does the AI RMF define risk?** _(keyword recall 0.667, answered)_

> The AI RMF defines risk as the combined measure of the likelihood of an event occurring and the magnitude or degree of its consequences.

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered)_

> Trustworthy AI systems are **valid and reliable; safe; secure and resilient; accountable and transparent; explainable and interpretable; privacy-enhanced; and fair, with harmful bias managed.**

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered)_

> Validation is the confirmation, through objective evidence, that an AI system fulfills the requirements for a specific intended use or application.

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered)_

> Reliability is the ability of an item to perform as required, without failure, for a given time interval under given conditions.

**q06. What are common security concerns for AI systems?** _(keyword recall 0.667, answered)_

> Common security concerns include adversarial examples, data poisoning, and attempts to exfiltrate models, training data, or other intellectual property through AI system endpoints. Risks also include unauthorized access or use, attacks on confidentiality, integrity, and availability, and machine-learning attacks such as evasion, model extraction, and membership inference.

**q07. What is the difference between explainability and interpretability?** _(keyword recall 0.000, answered)_

> Explainability describes how an AI system made a decision; interpretability explains why it made the decision and what that decision means in context.

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered)_

> Systemic bias, computational and statistical bias, and human-cognitive bias.

**q09. What does risk tolerance refer to?** _(keyword recall 0.667, answered)_

> Risk tolerance refers to an organization’s or AI actor’s readiness to bear risk in order to achieve its objectives.

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 0.500, answered)_

> Development and deployment should cease safely until the risks can be sufficiently managed.

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered)_

> GOVERN is the cross-cutting AI RMF function.

**q12. What is the purpose of the MAP function?** _(keyword recall 1.000, answered)_

> The MAP function establishes the context for identifying AI-related risks and their contributing factors. Its findings support risk prevention, decisions about whether an AI solution is appropriate, and the MEASURE and MANAGE functions.

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered)_

> The MEASURE function uses quantitative, qualitative, or mixed-method approaches to analyze, assess, benchmark, and monitor AI risks and impacts. It documents system functionality and trustworthiness, tracks relevant metrics, and uses testing and performance assessments—including uncertainty measures and benchmarks—to inform risk monitoring and response in the MANAGE function.

**q14. What does the MANAGE function entail?** _(keyword recall 1.000, answered)_

> The MANAGE function entails regularly allocating risk resources to mapped and measured risks, as defined by GOVERN. It uses measurement outcomes and contextual input to plan responses to, recovery from, and communication about incidents or events, while supporting risk monitoring, prioritization, and continual improvement.

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered)_

> A Target Profile describes the outcomes needed to achieve an organization’s desired AI risk management goals. It represents the target state of specific AI risk management activities.

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered)_

> TEVV stands for Test, Evaluation, Verification, and Validation. TEVV tasks are performed throughout the AI lifecycle, including during development and deployment.

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered)_

> The AI RMF will use a two-number system: the first number identifies the generation and changes only with major revisions (e.g., 1.0); a “.n” suffix tracks minor revisions (e.g., 1.1).

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered)_

> The OECD defines AI actors as those who play an active role in the AI system lifecycle, including organizations and individuals that deploy or operate AI.

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered)_

> Pre-trained models can increase statistical uncertainty and create challenges for bias management, scientific validity, and reproducibility. Their emergent properties can also make failure modes harder to predict.

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 1.000, answered)_

> Inscrutability can result from AI systems being opaque, with limited explainability or interpretability; from a lack of transparency or documentation in development or deployment; or from inherent uncertainties. It matters because these factors make risks harder to understand and measure. When risks are poorly defined or understood, they may be difficult to assess quantitatively or qualitatively—but that difficulty alone does not mean the system is either high- or low-risk.

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, abstained)_

> The provided context does not say how much funding NIST allocated to develop the AI RMF.

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> The provided context doesn’t specify a recommended programming language.
