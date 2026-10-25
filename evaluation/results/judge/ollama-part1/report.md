# RAG Evaluation Report

- **Date:** 2026-10-25 08:26 UTC
- **Dataset:** benchmark_part1.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** ollama/llama3
- **Judge model:** openai/gpt-6.1-sol
- **Candidates per retriever:** 12
- **Questions:** 26 (26 answerable, 0 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.885 | 0.923 | 0.923 | 0.769 | 0.846 | 0.846 | 0.904 | 15 |
| `bm25` | 0.808 | 0.923 | 0.923 | 0.654 | 0.865 | 0.904 | 0.865 | 1 |
| `hybrid_rrf` | 0.846 | 1.000 | 1.000 | 0.712 | 0.923 | 0.962 | 0.923 | 13 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.827 | 0.962 | 0.981 | 1.000 | 964 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.673 | 0.769 | 0.885 | 415 | 1316 | 2190 |
| `bm25` | 0.449 | 0.731 | 0.808 | 435 | 1318 | 2183 |
| `hybrid_rrf` | 0.635 | 0.750 | 0.942 | 395 | 1294 | 2196 |
| `hybrid_rrf_rerank` | 0.712 | 0.942 | 0.981 | 443 | 1366 | 2300 |

### Evidence@5 by Source

| Strategy | nist.ai.100-1.pdf | NIST.CSWP.29.pdf |
| --- | --- | --- |
| `vector` | 0.850 | 1.000 |
| `bm25` | 0.850 | 0.667 |
| `hybrid_rrf` | 0.950 | 0.917 |
| `hybrid_rrf_rerank` | 1.000 | 0.917 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.973 |
| Answer rate (answerable) | 0.962 |
| Abstention rate (unanswerable) | n/a |
| Citation rate (answered questions) | 1.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 27570 |
| LLM judge: correct | 1.000 |
| LLM judge: grounded in the passages | 0.960 |
| LLM judge: citations support their statements | 0.720 |
| LLM judge: no decision | 0 |

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
| c01 | 1.000 | 1.000 | 1.000 | 1.000 |
| c02 | 1.000 | 0.500 | 1.000 | 1.000 |
| c03 | 1.000 | 1.000 | 1.000 | 1.000 |
| c04 | 0.500 | 1.000 | 0.500 | 1.000 |
| c05 | 1.000 | 1.000 | 1.000 | 1.000 |
| c06 | 1.000 | 1.000 | 1.000 | 1.000 |

## Generated Answers

**q01. What are the four core functions of the NIST AI Risk Management Framework?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The four core functions of the NIST AI Risk Management Framework are GOVERN, MAP, MEASURE, and MANAGE. [1] This is stated in both [1] (page 25) and [2] (page 6), which provide a breakdown of these high-level functions into categories and subcategories to help organizations address AI risks.

**q02. How does the AI RMF define risk?** _(keyword recall 1.000, abstained)_

> According to the context, the AI RMF defines risk as a "composite measure of an event's probability of occurring and the magnitude or degree of the consequences of the corresponding event" [1]. This definition considers both the likelihood of occurrence and the negative impact or harm that would arise if the circumstance or event occurs [2].
>
> Note: The passage does not provide a specific mathematical formula for calculating risk, but rather defines it as a composite measure.

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> According to [1] page 17 and [2], the characteristics of trustworthy AI systems include:
>
> * Valid and reliable
> * Safe
> * Secure and resilient
> * Accountable and transparent
> * Explainable and interpretable
> * Privacy-enhanced
> * Fair with harmful bias managed
>
> These characteristics are also depicted in Fig. 4, as shown in [3] page 5.

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Validation is defined as "the 'confirmation, through the provision of objective evidence, that the requirements for a specific intended use or application have been fulfilled'" [1].

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> According to the context [1], reliability is defined as "the ability of an item to perform as required, without failure, for a given time interval, under given conditions" (Source: ISO/IEC TS 5723:2022).
>
> [1]

**q06. What are common security concerns for AI systems?** _(keyword recall 1.000, answered; judge: correct, not grounded, citations not supported)_

> Common security concerns for AI systems relate to adversarial examples, data poisoning, and the exfiltration of models, training data, or other intellectual property through AI system endpoints. Additionally, there may be concerns related to confidentiality, integrity, and availability of the system and its training and output data [1].
>
> Note: These are the only specific security concerns mentioned in the provided context.

**q07. What is the difference between explainability and interpretability?** _(keyword recall 0.500, answered; judge: correct, grounded, citations supported)_

> According to the provided context [2], the main difference between explainability and interpretability is that explainability answers the question of "how" a decision was made in the system, whereas interpretability answers the question of "why" a decision was made by the system and its meaning or context to the user.
>
> [2]

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> According to the context [1], the three major categories of AI bias identified by NIST are:
>
> * Systemic
> * Computational and statistical
> * Human-cognitive
>
> These categories can occur in the absence of prejudice, partiality, or discriminatory intent. [1]

**q09. What does risk tolerance refer to?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Risk tolerance refers to the organization's or AI actor's readiness to bear the risk in order to achieve its objectives. [1]
>
> This answer only references the provided context, specifically [1].

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Development and deployment of the AI system should cease in a safe manner until risks can be sufficiently managed. [1]

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The GOVERN function is described as cross-cutting in [2]. This means that it is designed to be infused throughout the other three functions and inform them.

**q12. What is the purpose of the MAP function?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> The purpose of the MAP function is to enhance an organization's ability to identify risks and broader contributing factors, as well as establish the context to frame risks related to an AI system. This enables negative risk prevention and informs decisions for processes such as model management, as well as an initial decision about appropriateness or the need for an AI solution.
>
> [1][2]

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> The MEASURE function employs quantitative, qualitative, or mixed-method tools, techniques, and methodologies to analyze, assess, benchmark, and monitor AI risk and related impacts. [1][2]
>
> It uses knowledge relevant to AI risks identified in the MAP function and informs the MANAGE function. AI systems should be tested before their deployment and regularly while in operation.

**q14. What does the MANAGE function entail?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The MANAGE function entails allocating risk resources to mapped and measured risks on a regular basis and as defined by the GOVERN function. It also includes plans to respond to, recover from, and communicate about incidents or events [1].
>
> Additionally, it utilizes contextual information gleaned from expert consultation and input from relevant AI actors established in GOVERN and carried out in MAP to decrease the likelihood of system failures and negative impacts [1].

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> A Target Profile in the AI RMF indicates the outcomes needed to achieve the desired or target AI risk management goals. [2]

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> TEVV stands for Test, Evaluation, Verification, and Validation. According to the provided context [1][2], TEVV tasks are performed throughout the AI lifecycle, which includes development (model building), deployment (system validation and integration in production), design, planning, and data.
>
> [1]
> [2]

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The Artificial Intelligence Risk Management Framework (AI RMF) will employ a two-number versioning system. The first number represents the generation of the AI RMF and its companion documents, which will change only with major revisions. Minor revisions will be tracked using '.n' after the generation number.
>
> [1]

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> According to the context [1], AI actors are defined by the Organisation for Economic Co-operation and Development (OECD) as 'those who play an active role in the AI system lifecycle, including organizations and individuals that deploy or operate AI'.

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> Pre-trained models can advance research, increase accuracy, and improve resilience when compared to other models and approaches. However, this can also increase levels of statistical uncertainty and cause issues with bias management, scientific validity, and reproducibility [2]. Additionally, the use of pre-trained models can lead to higher degrees of difficulty in predicting failure modes for emergent properties of large-scale pre-trained models [3].
>
> [Reference: nist.ai.100-1.pdf, page 43]

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> According to the context, inscrutability in AI systems can be caused by the opaque nature of AI systems (limited explainability or interpretability), lack of transparency or documentation in AI system development or deployment, or inherent uncertainties in AI systems [1]. This matters for risk measurement because it complicates the process.

**c01. What are the six Functions of the NIST Cybersecurity Framework 2.0 Core?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The six CSF Functions of the NIST Cybersecurity Framework 2.0 Core are: Govern, Identify, Protect, Detect, Respond, and Recover. [2]

**c02. What does the GOVERN Function cover in the Cybersecurity Framework?** _(keyword recall 0.800, answered; judge: correct, grounded, citations supported)_

> According to the context, the GOVERN Function covers an organization's "cybersecurity risk management strategy, expectations, and policy are established, communicated, and monitored" [1]. Additionally, it supports organizational risk communication with executives, including discussions about risk management strategies, roles, responsibilities, and authorities, policies, and oversight [2].

**c03. Why is GOVERN shown at the center of the CSF Functions wheel?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> GOVERN is shown at the center of the CSF Functions wheel because it informs how an organization will implement the other five Functions. [1]
>
> This answer is supported by the text in [1], which states that "GOVERN is in the center of the wheel because it informs how an organization will implement the other five Functions."

**c04. What are the four CSF Tiers?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> The four CSF Tiers are Partial (Tier 1), Risk Informed (Tier 2), Repeatable (Tier 3), and Adaptive (Tier 4). [1][2][3]

**c05. What is a Target Profile in the Cybersecurity Framework?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> A Target Profile specifies the desired outcomes that an organization has selected and prioritized for achieving its cybersecurity risk management objectives. It considers anticipated changes to the organization's cybersecurity posture, such as new requirements, new technology adoption, and threat intelligence trends.
>
> [1][3]

**c06. What is a CSF Community Profile and how can an organization use one?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> A CSF Community Profile is a baseline of CSF outcomes that is created and published to address shared interests and goals among a number of organizations. An organization can use a Community Profile as the basis for its own Target Profile.
>
> [1][2]
>
> It is typically developed for a particular sector, subsector, technology, threat type, or other use case.
