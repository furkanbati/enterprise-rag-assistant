# RAG Evaluation Report

- **Date:** 2026-10-25 08:55 UTC
- **Dataset:** chunking_benchmark.jsonl
- **Embedding model:** openai/text-embedding-3-small
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** openai/gpt-6-luna
- **Judge model:** openai/gpt-6.1-sol
- **Candidates per retriever:** 12
- **Questions:** 52 (48 answerable, 4 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.958 | 0.979 | 0.979 | 0.833 | 0.938 | 0.969 | 0.969 | 44 |
| `bm25` | 0.875 | 0.938 | 0.938 | 0.750 | 0.865 | 0.885 | 0.906 | 2 |
| `hybrid_rrf` | 0.979 | 1.000 | 1.000 | 0.844 | 0.927 | 0.958 | 0.990 | 25 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.865 | 0.958 | 0.969 | 1.000 | 2082 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.569 | 0.806 | 0.857 | 421 | 1456 | 2452 |
| `bm25` | 0.556 | 0.778 | 0.820 | 439 | 1333 | 2221 |
| `hybrid_rrf` | 0.584 | 0.843 | 0.910 | 420 | 1433 | 2324 |
| `hybrid_rrf_rerank` | 0.686 | 0.909 | 0.930 | 430 | 1341 | 2269 |

### Evidence@5 by Source

| Strategy | nist.ai.100-1.pdf | NIST.CSWP.29.pdf | FOMCpresconf20240918.pdf |
| --- | --- | --- | --- |
| `vector` | 0.900 | 0.910 | 0.744 |
| `bm25` | 0.850 | 0.757 | 0.839 |
| `hybrid_rrf` | 0.950 | 0.888 | 0.875 |
| `hybrid_rrf_rerank` | 1.000 | 0.921 | 0.839 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.775 |
| Answer rate (answerable) | 0.979 |
| Abstention rate (unanswerable) | 1.000 |
| Citation rate (answered questions) | 1.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 1678 |
| LLM judge: correct | 0.936 |
| LLM judge: grounded in the passages | 1.000 |
| LLM judge: citations support their statements | 1.000 |
| LLM judge: no decision | 0 |

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
| c01 | 1.000 | 1.000 | 1.000 | 1.000 |
| c02 | 1.000 | 0.500 | 1.000 | 1.000 |
| c03 | 1.000 | 1.000 | 1.000 | 1.000 |
| c04 | 1.000 | 1.000 | 1.000 | 1.000 |
| c05 | 1.000 | 1.000 | 1.000 | 1.000 |
| c06 | 1.000 | 1.000 | 1.000 | 1.000 |
| c07 | 1.000 | 1.000 | 1.000 | 1.000 |
| c08 | 1.000 | 1.000 | 1.000 | 1.000 |
| c09 | 1.000 | 1.000 | 1.000 | 1.000 |
| c10 | 1.000 | 1.000 | 1.000 | 1.000 |
| c11 | 1.000 | 1.000 | 1.000 | 1.000 |
| c12 | 1.000 | 0.000 | 1.000 | 1.000 |
| c13 | 1.000 | 1.000 | 1.000 | 1.000 |
| c14 | 1.000 | 1.000 | 1.000 | 1.000 |
| f01 | 1.000 | 1.000 | 1.000 | 1.000 |
| f02 | 1.000 | 1.000 | 1.000 | 1.000 |
| f03 | 1.000 | 1.000 | 1.000 | 1.000 |
| f04 | 1.000 | 1.000 | 1.000 | 1.000 |
| f05 | 1.000 | 1.000 | 1.000 | 1.000 |
| f06 | 1.000 | 1.000 | 1.000 | 1.000 |
| f07 | 1.000 | 1.000 | 1.000 | 1.000 |
| f08 | 1.000 | 1.000 | 1.000 | 1.000 |
| f09 | 1.000 | 1.000 | 1.000 | 1.000 |
| f10 | 1.000 | 1.000 | 1.000 | 1.000 |
| f11 | 1.000 | 1.000 | 1.000 | 1.000 |
| f12 | 1.000 | 1.000 | 1.000 | 1.000 |
| f13 | 1.000 | 1.000 | 1.000 | 1.000 |
| f14 | 1.000 | 1.000 | 1.000 | 1.000 |

## Generated Answers

**q01. What are the four core functions of the NIST AI Risk Management Framework?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The four core functions are GOVERN, MAP, MEASURE, and MANAGE. [1][2]

**q02. How does the AI RMF define risk?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The AI RMF defines risk as a composite measure of the probability that an event will occur and the magnitude or degree of its consequences. [1]

**q03. What are the characteristics of trustworthy AI systems?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Trustworthy AI systems are valid and reliable; safe; secure and resilient; accountable and transparent; explainable and interpretable; privacy-enhanced; and fair, with harmful bias managed. [1][2]

**q04. How is validation defined in the context of AI systems?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Validation is the confirmation, through objective evidence, that requirements for a specific intended use or application have been fulfilled. [1]

**q05. What is the definition of reliability used by the framework?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Reliability is the “ability of an item to perform as required, without failure, for a given time interval, under given conditions.” [1]

**q06. What are common security concerns for AI systems?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> Common security concerns include adversarial examples, data poisoning, and attempts to exfiltrate models, training data, or other intellectual property through AI system endpoints. [1] Other concerns include threats to confidentiality, integrity, and availability, as well as attacks such as evasion, model extraction, and membership inference. [1][2][3]

**q07. What is the difference between explainability and interpretability?** _(keyword recall 0.000, answered; judge: correct, grounded, citations supported)_

> Explainability describes how an AI system works and how it made a decision; interpretability describes what the system’s output means in the context of its purpose, including why a decision was made. [1][2]

**q08. What are the three major categories of AI bias identified by NIST?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The three major categories are systemic bias, computational and statistical bias, and human-cognitive bias. [1]

**q09. What does risk tolerance refer to?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> Risk tolerance refers to an organization’s or AI actor’s readiness to bear risk in order to achieve its objectives. [1]

**q10. What should happen when an AI system presents unacceptable negative risk levels?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Development and deployment should cease in a safe manner until the risks can be sufficiently managed. [1]

**q11. Which AI RMF function is described as cross-cutting?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> GOVERN is the AI RMF function described as cross-cutting. [2]

**q12. What is the purpose of the MAP function?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The MAP function establishes the context for framing AI-system risks and helps identify risks and contributing factors. Its findings inform prevention and decisions about whether an AI solution is appropriate, and provide the basis for the MEASURE and MANAGE functions. [1][2][3]

**q13. What does the MEASURE function do?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The MEASURE function uses quantitative, qualitative, or mixed methods to analyze, assess, benchmark, and monitor AI risks and related impacts, using knowledge from MAP to inform MANAGE. It involves testing AI systems before deployment and regularly during operation, tracking trustworthiness and social-impact metrics, and documenting rigorous testing, performance, uncertainty, benchmarks, and results. [1][2][3]

**q14. What does the MANAGE function entail?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> The MANAGE function entails regularly allocating resources to mapped and measured risks, as defined by GOVERN. It includes planning how to respond to, recover from, and communicate about incidents or events, using relevant contextual information to reduce the likelihood of system failures and negative impacts. [1]

**q15. What is a Target Profile in the AI RMF?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> A Target Profile describes the outcomes needed to achieve an organization’s desired AI risk management goals. [1]

**q16. What does TEVV stand for and when are TEVV tasks performed?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> TEVV stands for **Test, Evaluation, Verification, and Validation**. These tasks are performed throughout the AI lifecycle. [1]

**q17. What versioning system will the AI RMF use to track changes?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The AI RMF uses a two-number versioning system: the first number identifies the generation and changes only for major revisions, while minor revisions use “.n” after it (for example, 1.1). [1]

**q18. How does the OECD define AI actors?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The OECD defines AI actors as those who play an active role in the AI system lifecycle, including organizations and individuals that deploy or operate AI. [1]

**q19. How can pre-trained models increase AI-specific risks compared to traditional software?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Pre-trained models can increase statistical uncertainty and create challenges with bias management, scientific validity, and reproducibility. Their emergent properties can also make failure modes harder to predict. [2]

**q20. What causes inscrutability in AI systems and why does it matter for risk measurement?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Inscrutability can result from an AI system’s opaque nature (limited explainability or interpretability), lack of transparency or documentation in its development or deployment, or inherent uncertainties. It matters because it can complicate risk measurement. [1]

**c01. What are the six Functions of the NIST Cybersecurity Framework 2.0 Core?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The six Functions are Govern, Identify, Protect, Detect, Respond, and Recover. [2]

**c02. What does the GOVERN Function cover in the Cybersecurity Framework?** _(keyword recall 0.200, answered; judge: correct, grounded, citations supported)_

> The GOVERN Function covers establishing, communicating, and monitoring an organization’s cybersecurity risk management strategy, expectations, and policies. It also guides how the organization prioritizes the outcomes of the other CSF Functions in light of its mission and stakeholder expectations. [1]

**c03. Why is GOVERN shown at the center of the CSF Functions wheel?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> GOVERN is at the center because it informs how the organization implements and prioritizes the other five Functions, in the context of its mission and stakeholder expectations. [1][3]

**c04. What are the four CSF Tiers?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The four CSF Tiers are Partial (Tier 1), Risk Informed (Tier 2), Repeatable (Tier 3), and Adaptive (Tier 4). [1][2]

**c05. What is a Target Profile in the Cybersecurity Framework?** _(keyword recall 0.500, answered; judge: correct, grounded, citations supported)_

> A Target Profile is part of an Organizational Profile that specifies the desired cybersecurity outcomes an organization has selected and prioritized to meet its cybersecurity risk management objectives. [2]

**c06. What is a CSF Community Profile and how can an organization use one?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> A CSF Community Profile is a published baseline of CSF outcomes developed around shared interests and goals, often for a particular sector, technology, threat type, or other use case. [1][2] An organization can use it as the basis for its own Target Profile. [1][2]

**c07. What steps does the CSF describe for using an Organizational Profile?** _(keyword recall 0.600, answered; judge: incorrect, grounded, citations supported)_

> The CSF describes these steps: scope the Organizational Profile by documenting the high-level facts and assumptions; use it to understand and prioritize cybersecurity outcomes in light of the organization’s objectives, stakeholders, threats, and requirements; then implement an action plan to close gaps and update the Profile. The organization can repeat the process as needed for continual improvement. [2][3][1]

**c08. What are Informative References in the CSF?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Informative References are mappings that show relationships between CSF Core outcomes and existing standards, guidelines, regulations, or other content. They help inform how an organization may achieve those outcomes. [1][2] They may be sector- or technology-specific and can come from NIST or another organization. [3]

**c09. What are CSF Quick-Start Guides?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> CSF Quick-Start Guides are brief resources on specific CSF-related topics that offer actionable first steps to help organizations use the CSF and improve cybersecurity risk management. [1][2][3]

**c10. What was the Cybersecurity Framework called before version 2.0?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Before version 2.0, it was called the “Framework for Improving Critical Infrastructure Cybersecurity.” [1]

**c11. In which ways can an organization handle risk according to the CSF?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> An organization can handle negative risks by mitigating, transferring, avoiding, or accepting them; it can handle positive risks by realizing, sharing, enhancing, or accepting them. [1]

**c12. How does the Cybersecurity Framework relate to the NIST AI RMF?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The CSF recognizes that AI introduces cybersecurity, privacy, and other risks, and identifies the NIST AI RMF as a framework developed to help address them. [3] The AI RMF also uses Functions, Categories, and Subcategories to describe AI outcomes and help manage AI-related risks. [1]

**c13. Which CSF Category covers cybersecurity supply chain risk management?** _(keyword recall 0.500, answered; judge: correct, grounded, citations supported)_

> The CSF Category is **GV.SC (Cybersecurity Supply Chain Risk Management)**. [1]

**c14. What does the DETECT Function enable?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The DETECT Function enables timely discovery and analysis of anomalies, indicators of compromise, and other potentially adverse events that may signal cybersecurity attacks or incidents. [1]

**f01. By how much did the FOMC lower the federal funds rate in September 2024, and to what target range?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> The FOMC lowered the federal funds rate by ½ percentage point, to a target range of 4¾% to 5%. [1]

**f02. What was the peak of inflation and where did it stand as of August 2024?** _(keyword recall 0.000, answered; judge: correct, grounded, citations supported)_

> Inflation peaked at 7% and stood at an estimated 2.2% as of August 2024. [1]

**f03. What federal funds rate did the median participant project for the end of 2024 and the end of 2025?** _(keyword recall 0.000, answered; judge: correct, grounded, citations supported)_

> The median participant projected a federal funds rate of 4.4% at the end of 2024 and 3.4% at the end of 2025. [1]

**f04. How did the median unemployment projection in the SEP change compared with June?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The median unemployment projection for the end of this year rose by four-tenths of a percentage point compared with June, to 4.4 percent. [1]

**f05. How many FOMC participants wrote down three or more rate cuts for this year?** _(keyword recall 0.500, answered; judge: correct, grounded, citations supported)_

> 17 of the 19 participants wrote down three or more rate cuts for this year. [1]

**f06. Why is the Fed continuing balance sheet runoff while cutting rates?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The Fed views balance-sheet runoff and rate cuts as forms of normalization that can happen at the same time. [2] Reserves remain abundant and are expected to stay so, while the balance-sheet shrinkage has come mainly from the overnight reverse repo facility; Powell said this was not a reason to stop runoff. [3]

**f07. Which labor market indicators did Powell cite as signs of a solid labor market?** _(keyword recall 0.250, answered; judge: incorrect, grounded, citations supported)_

> Powell specifically cited quits returning to normal levels. He also referred generally to many employment indicators, without naming them individually, as evidence of a solid labor market. [1]

**f08. Why has housing inflation been slow to come down?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> Housing inflation has been slow to come down because lower market rents take time to show up in renewals of existing leases, and those renewing leases haven’t fallen as much as expected; owner’s equivalent rent has also remained high. [1][3] Powell said this pass-through may take several years rather than just one or two annual lease-renewal cycles. [3]

**f09. Why is the housing market partly frozen?** _(keyword recall 0.333, answered; judge: correct, grounded, citations supported)_

> The housing market is partly frozen because homeowners with low mortgage rates are reluctant to sell, since replacing their mortgages would be expensive. [1]

**f10. According to Powell, why do democracies have independent central banks?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> Powell says independent central banks help prevent monetary policy from favoring those in political office, and countries with independent central banks tend to have lower inflation. [1]

**f11. Does Powell support Vice Chair Barr's Basel III endgame changes, and when do they aim to conclude?** _(keyword recall 0.667, abstained)_

> Powell said the changes were negotiated among the agencies with his support and involvement, and that they planned to re-propose them and take comments. [2] The context does not say when they aim to conclude.

**f12. Does the Fed think it has fallen behind on rate cuts?** _(keyword recall 0.000, answered; judge: incorrect, grounded, citations supported)_

> Powell said the Fed had been patient about reducing rates and waited until it was confident inflation was moving sustainably toward 2 percent. [3]

**f13. Does Powell see an elevated likelihood of a recession?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> No. Powell said he doesn’t see anything in the economy suggesting that the likelihood of a downturn is elevated. [1]

**f14. Would the Fed have cut rates in July if it had seen the July employment report before that meeting?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The Fed might well have cut rates if it had seen the July employment report before the meeting, but it did not make that decision. [1][3]

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, abstained)_

> I don’t know; the provided context does not state how much funding NIST allocated to develop the AI RMF. [1][3]

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> I don’t know; the provided context does not say which programming language NIST recommends for building machine learning models. [1][2][3]

**u01. How many organizations had adopted CSF 2.0 by the end of 2024?** _(unanswerable, abstained)_

> I don’t know; the provided context does not state how many organizations had adopted CSF 2.0 by the end of 2024. [1][2][3]

**u02. What unemployment rate for Germany was discussed in the September 2024 press conference?** _(unanswerable, abstained)_

> The context discusses U.S. unemployment, not Germany’s. I don’t know the unemployment rate for Germany. [1][2][3]
