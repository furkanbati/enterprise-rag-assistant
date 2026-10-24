# RAG Evaluation Report

- **Date:** 2026-10-24 15:08 UTC
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
| `vector` | 0.900 | 0.900 | 0.900 | 0.850 | 0.875 | 0.875 | 0.900 | 10 |
| `bm25` | 0.800 | 0.900 | 0.900 | 0.700 | 0.850 | 0.900 | 0.850 | 1 |
| `hybrid_rrf` | 0.850 | 1.000 | 1.000 | 0.775 | 0.925 | 0.975 | 0.925 | 11 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.900 | 0.975 | 1.000 | 1.000 | 947 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.975 |
| Answer rate (answerable) | 1.000 |
| Abstention rate (unanswerable) | 1.000 |
| Citation rate (answered questions) | 1.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 27273 |

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

**q01. What are the four core functions of the NIST AI Risk Management Framework?** _(keyword recall 1.000, answered)_

> The four core functions of the NIST AI Risk Management Framework are GOVERN, MAP, MEASURE, and MANAGE. [1][2]
>
> These functions are further broken down into categories and subcategories to help organizations address the risks of AI systems in practice.

**q02. How does the AI RMF define risk?** _(keyword recall 1.000, answered)_

> According to the context, the AI RMF defines risk as "the composite measure of an event's probability of occurring and the magnitude or degree of the consequences of the corresponding event" [1]. This definition also takes into account that "risk is a function of 1) the negative impact, or magnitude of harm, that would arise if the circumstance or event occurs and 2) the likelihood of occurrence" [2].
>
> In other words, risk in the AI RMF context is a combination of the probability of an event occurring and the severity of its consequences.

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered)_

> According to the provided context [1], the characteristics of trustworthy AI systems include:
>
> * Valid and reliable
> * Safe
> * Secure and resilient
> * Accountable and transparent
> * Explainable and interpretable
> * Privacy-enhanced
> * Fair with harmful bias managed
>
> These characteristics are mentioned in both [1] and [2] as necessary conditions for creating trustworthy AI. Additionally, Fig. 4 in [3] illustrates the characteristics of trustworthy AI systems, with "Valid & Reliable" being a necessary condition and "Accountable & Transparent" relating to all other characteristics.

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered)_

> Validation is defined as "the 'confirmation, through the provision of objective evidence, that the requirements for a specific intended use or application have been fulfilled'" [1].

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered)_

> According to the context [1], reliability is defined as "the ability of an item to perform as required, without failure, for a given time interval, under given conditions" (Source: ISO/IEC TS 5723:2022).

**q06. What are common security concerns for AI systems?** _(keyword recall 1.000, answered)_

> Common security concerns for AI systems include adversarial examples, data poisoning, and the exfiltration of models, training data, or other intellectual property through AI system endpoints [1].

**q07. What is the difference between explainability and interpretability?** _(keyword recall 1.000, answered)_

> According to the context [1], explainability refers to a representation of the mechanisms underlying AI systems' operation, whereas interpretability refers to the meaning of AI systems' output in the context of their designed functional purposes.
>
> In other words, explainability answers the question of "how" a decision was made, while interpretability answers the question of "why" a decision was made and its meaning or context to the user. [2]
>
> So, the main difference between explainability and interpretability is that explainability focuses on the mechanism behind the AI system's operation, whereas interpretability focuses on the meaning and context of the AI system's output.
>
> [Cites: [1], [2]]

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered)_

> According to the provided context, the three major categories of AI bias identified by NIST are:
>
> * Systemic
> * Computational and statistical
> * Human-cognitive
>
> These categories can occur in the absence of prejudice, partiality, or discriminatory intent. [1]
>
> The other two passages do not provide new information about the types of biases, but rather describe their association with transparency and fairness, and explain that these biases can be present throughout the AI lifecycle and broader society. [2][3]

**q09. What does risk tolerance refer to?** _(keyword recall 1.000, answered)_

> Risk tolerance refers to the organization's or AI actor's readiness to bear the risk in order to achieve its objectives.
>
> [1]

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 1.000, answered)_

> Development and deployment should cease in a safe manner until risks can be sufficiently managed. [1]

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered)_

> The AI RMF function that is described as cross-cutting is Governance. [2]

**q12. What is the purpose of the MAP function?** _(keyword recall 0.500, answered)_

> The purpose of the MAP function is to enhance an organization's ability to identify risks and broader contributing factors, by incorporating perspectives from a diverse internal team and engagement with those external to the team that developed or deployed the AI system. [1]
>
> This function also enables negative risk prevention and informs decisions for processes such as model management, as well as an initial decision about appropriateness or the need for an AI solution. [2]

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered)_

> The MEASURE function employs quantitative, qualitative, or mixed-method tools, techniques, and methodologies to analyze, assess, benchmark, and monitor AI risk and related impacts. [1][3]
>
> It uses knowledge relevant to AI risks identified in the MAP function and informs the MANAGE function. AI systems should be tested before their deployment and regularly while in operation.

**q14. What does the MANAGE function entail?** _(keyword recall 1.000, answered)_

> The MANAGE function entails allocating risk resources to mapped and measured risks on a regular basis and as defined by the GOVERN function. Risk treatment comprises plans to respond to, recover from, and communicate about incidents or events.
>
> [1]

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered)_

> A Target Profile in the AI RMF indicates the outcomes needed to achieve the desired or target AI risk management goals. [1]
>
> In other words, it's a description of the desired state for specific AI risk management activities within a given sector, industry, organization, or application context, which helps organizations decide how best to manage AI risk and meet their objectives. [2]

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered)_

> TEVV stands for Test, Evaluation, Verification, and Validation. According to the provided context [1][2], TEVV tasks are performed throughout the AI lifecycle, which includes development, deployment, and other phases such as design, planning, and data collection.
>
> [1]
> [2]

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered)_

> The AI RMF will employ a two-number versioning system to track and identify major and minor changes. The first number will represent the generation of the AI RMF and its companion documents, and the second number will be used for minor revisions.
>
> [1]

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered)_

> According to the provided context, the Organisation for Economic Co-operation and Development (OECD) defines "AI actors" as 'those who play an active role in the AI system lifecycle, including organizations and individuals that deploy or operate AI' [1].

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered)_

> Pre-trained models can advance research, improve performance, and increase levels of statistical uncertainty, causing issues with bias management, scientific validity, and reproducibility [2]. Additionally, using pre-trained models can also increase the difficulty in predicting failure modes for emergent properties of large-scale pre-trained models [3].
>
> [References: [2], [3]]

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 1.000, answered)_

> Inscrutability in AI systems can result from the opaque nature of AI systems (limited explainability or interpretability), lack of transparency or documentation in AI system development or deployment, or inherent uncertainties in AI systems.
>
> [1]
>
> This inscrutability can complicate risk measurement.

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, abstained)_

> I don't know. The provided context does not mention any information about the funding allocated to develop the AI RMF.

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> I don't know. The provided context only discusses the NIST Cybersecurity Framework (CSF) and its purpose, without mentioning any specific programming languages or machine learning models. [1][2]
