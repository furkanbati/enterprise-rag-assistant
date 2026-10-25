# RAG Evaluation Report

- **Date:** 2026-10-25 09:11 UTC
- **Dataset:** benchmark_part2.jsonl
- **Embedding model:** ollama/nomic-embed-text
- **Chunking:** sentence-ctx
- **Reranker:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Chat model:** ollama/llama3
- **Judge model:** openai/gpt-6.1-sol
- **Candidates per retriever:** 12
- **Questions:** 26 (22 answerable, 4 unanswerable)

## Retrieval

Relevance is judged at page level against the labelled dataset. Unanswerable questions are excluded from retrieval metrics.

| Strategy | Hit@1 | Hit@3 | Hit@5 | Recall@1 | Recall@3 | Recall@5 | MRR@5 | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `vector` | 1.000 | 1.000 | 1.000 | 0.909 | 0.977 | 0.977 | 1.000 | 14 |
| `bm25` | 0.955 | 0.955 | 0.955 | 0.864 | 0.864 | 0.864 | 0.955 | 1 |
| `hybrid_rrf` | 0.955 | 1.000 | 1.000 | 0.864 | 0.909 | 0.932 | 0.977 | 13 |
| `hybrid_rrf_rerank` | 1.000 | 1.000 | 1.000 | 0.909 | 0.955 | 0.955 | 1.000 | 708 |

## Evidence Coverage

Share of the labelled evidence sentences found in the top-k chunks. Unlike the page-level metrics above, this changes with chunking. Context chars is the text the top-k chunks send to the model; larger chunks raise recall by sending more.

| Strategy | Evidence@1 | Evidence@3 | Evidence@5 | Context chars@1 | Context chars@3 | Context chars@5 |
| --- | --- | --- | --- | --- | --- | --- |
| `vector` | 0.439 | 0.835 | 0.870 | 394 | 1336 | 2181 |
| `bm25` | 0.683 | 0.834 | 0.834 | 443 | 1351 | 2265 |
| `hybrid_rrf` | 0.524 | 0.852 | 0.902 | 431 | 1342 | 2157 |
| `hybrid_rrf_rerank` | 0.657 | 0.870 | 0.870 | 415 | 1325 | 2236 |

### Evidence@5 by Source

| Strategy | NIST.CSWP.29.pdf | FOMCpresconf20240918.pdf |
| --- | --- | --- |
| `vector` | 0.925 | 0.839 |
| `bm25` | 0.825 | 0.839 |
| `hybrid_rrf` | 0.950 | 0.875 |
| `hybrid_rrf_rerank` | 0.925 | 0.839 |

## Answer Generation

Answers generated with `hybrid_rrf_rerank` using the top 3 chunks.

| Metric | Value |
|---|---|
| Keyword recall (answerable) | 0.694 |
| Answer rate (answerable) | 0.955 |
| Abstention rate (unanswerable) | 1.000 |
| Citation rate (answered questions) | 1.000 |
| Answers with invalid citations | 0 |
| Mean generation latency (ms) | 29615 |
| LLM judge: correct | 0.550 |
| LLM judge: grounded in the passages | 0.700 |
| LLM judge: citations support their statements | 0.700 |
| LLM judge: no decision | 3 |

## Per-question Reciprocal Rank

| Question | vector | bm25 | hybrid_rrf | hybrid_rrf_rerank |
| --- | --- | --- | --- | --- |
| c07 | 1.000 | 1.000 | 1.000 | 1.000 |
| c08 | 1.000 | 1.000 | 1.000 | 1.000 |
| c09 | 1.000 | 1.000 | 1.000 | 1.000 |
| c10 | 1.000 | 1.000 | 1.000 | 1.000 |
| c11 | 1.000 | 1.000 | 1.000 | 1.000 |
| c12 | 1.000 | 0.000 | 0.500 | 1.000 |
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

**c07. What steps does the CSF describe for using an Organizational Profile?** _(keyword recall 0.600, answered; judge: incorrect, grounded, citations supported)_

> According to the provided context [2], one way an organization could use an Organizational Profile to help inform continuous improvement of its cybersecurity is by:
>
> * Scoping the Organizational Profile
> * Documenting high-level facts and assumptions on which the Profile will be based to define its scope.
>
> Additionally, according to [1], an action plan may involve updating the Organizational Profile to address gaps and move the organization toward the Target Profile.

**c08. What are Informative References in the CSF?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> Informative References in the CSF are mappings that indicate relationships between the Core and various standards, guidelines, regulations, or other content. They help inform how an organization may achieve the Core's outcomes. [1]
>
> Additionally, Informative References can be sector- or technology-specific and may be produced by NIST or another organization. They provide a mapping that indicates a relationship between a CSF Core outcome and an existing standard, guideline, regulation, or other content. [2][3]

**c09. What are CSF Quick-Start Guides?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> According to [2], CSF Quick-Start Guides (QSGs) are brief documents that give actionable guidance on specific CSF-related topics. They can help an organization implement the CSF by distilling specific portions of the framework into "first steps" for improving their cybersecurity posture and managing associated risks.

**c10. What was the Cybersecurity Framework called before version 2.0?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The Cybersecurity Framework was called "Framework for Improving Critical Infrastructure Cybersecurity" before version 2.0. [1]

**c11. In which ways can an organization handle risk according to the CSF?** _(keyword recall 1.000, answered; judge: incorrect, not grounded, citations not supported)_

> According to the context, an organization may choose to handle risk in one or more ways by:
>
> * Mitigating negative risks
> * Transferring negative risks
> * Avoiding negative risks
> * Accepting negative risks
> * Realizing positive risks
> * Sharing positive risks
> * Enhancing positive risks
> * Accepting positive risks
>
> These options are mentioned on page 15 of the NIST.CSWP.29.pdf [1].
>
> Additionally, the context suggests that an organization can also handle risk by increasing revenue through actions to reduce cybersecurity risk, as mentioned in page 8 of the same document [2].

**c12. How does the Cybersecurity Framework relate to the NIST AI RMF?** _(keyword recall 0.250, answered; judge: incorrect, not grounded, citations not supported)_

> The Cybersecurity Framework (CSF) relates to the NIST Artificial Intelligence Risk Management Framework (AI RMF) in that they are both developed by NIST. The CSF is mentioned as a framework used for managing risks related to AI, and the AI RMF was developed to help address cybersecurity and privacy risks associated with artificial intelligence [2]. Additionally, the AI RMF will continue to align with applicable international standards, guidelines, and practices, including the Cybersecurity Framework [3].
>
> [1][2]

**c13. Which CSF Category covers cybersecurity supply chain risk management?** _(keyword recall 1.000, answered; judge: correct, grounded, citations not supported)_

> C-SCRM (Cybersecurity Supply Chain Risk Management) is covered under the C-SCRM Category in the CSF framework. [1][2]
>
> Specifically, the C-SCRM Category is mentioned in the Subcategories within the CSF C-SCRM Category [GV.SC] on page 16 of NIST.CSWP.29.pdf.

**c14. What does the DETECT Function enable?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The DETECT Function enables the timely discovery and analysis of anomalies, indicators of compromise, and other potentially adverse events that may indicate that cybersecurity attacks and incidents are occurring [1].

**f01. By how much did the FOMC lower the federal funds rate in September 2024, and to what target range?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The FOMC lowered the federal funds rate by ½ percentage point to a target range of 4¾ percent to 5 percent. [1]

**f02. What was the peak of inflation and where did it stand as of August 2024?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The peak of inflation was 7 percent, and as of August 2024, it stood at an estimated 2.2 percent.
>
> [1]

**f03. What federal funds rate did the median participant project for the end of 2024 and the end of 2025?** _(keyword recall 0.000, abstained)_

> According to the context, the median participant projected that the appropriate level of the federal funds rate will be:
>
> * 4.4% at the end of this year [1]
> * 3.4% at the end of 2025 [1]
>
> No information is provided regarding the likelihood of cheap money becoming the norm or any other related topic, as it falls outside the scope of the median participant's projections [2].

**f04. How did the median unemployment projection in the SEP change compared with June?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> The median unemployment rate in the SEP was projected to be four-tenths higher at 4.4 percent at the end of this year, compared to the previous projection in June [1].
>
> So, the median unemployment projection in the SEP increased by four-tenths compared with June.

**f05. How many FOMC participants wrote down three or more rate cuts for this year?** _(keyword recall 0.000, answered; judge: incorrect, not grounded, citations not supported)_

> According to the context, seven of the 19 FOMC participants wrote down three or more rate cuts for this year. [1]

**f06. Why is the Fed continuing balance sheet runoff while cutting rates?** _(keyword recall 0.333, answered; judge: incorrect, grounded, citations supported)_

> According to Chair Powell, the shrinkage in the Fed's balance sheet has come out of the overnight RRP facility and reserves have remained stable. He mentions that they're not thinking about stopping runoff because of this [3]. This suggests that the Fed is continuing balance sheet runoff despite cutting rates.
>
> [3]

**f07. Which labor market indicators did Powell cite as signs of a solid labor market?** _(keyword recall 0.250, answered; judge: incorrect, not grounded, citations supported)_

> According to Chair Powell's statement, "quits have come back down to normal levels" and there are "many, many employment indicators" that suggest this is still a solid labor market [1]. However, he does not specifically mention which labor market indicators he is referring to.

**f08. Why has housing inflation been slow to come down?** _(keyword recall 1.000, answered; judge: incorrect, not grounded, citations not supported)_

> According to Chair Powell, housing inflation is slow to come down because "the leases that are rolling over are not coming down as much" and OER (other economic rent) is coming in high [1]. Additionally, it's taking time for lower market rents to get into the system, but the direction of travel is clear, and once market rents remain relatively low, inflation will show up over time [3].
>
> [1]
> [3]

**f09. Why is the housing market partly frozen?** _(keyword recall 1.000, answered; judge: correct, grounded, citations supported)_

> According to Chair Powell, the housing market is partly frozen because of lock-in with low rates [1]. People don't want to sell their homes because it would be quite expensive to refinance with a very low mortgage.

**f10. According to Powell, why do democracies have independent central banks?** _(keyword recall 0.667, answered; judge: correct, grounded, citations supported)_

> According to Chair Powell, democracies have independent central banks because insulating the central bank from direct control by political authorities avoids making monetary policy in a way that favors people who are in office as opposed to people who are not in office. This is stated on page 1 of the transcript [1].
>
> Additionally, it is mentioned that this institutional arrangement has been good for the public and Powell hopes it will continue [3].

**f11. Does Powell support Vice Chair Barr's Basel III endgame changes, and when do they aim to conclude?** _(keyword recall 0.667, answered; judge: incorrect, grounded, citations not supported)_

> According to the transcript, the answer is "yes", Chair Powell supports Vice Chair Barr's Basel III endgame changes [1]. Additionally, it seems that the Fed aims to re-propose these changes after negotiation with agencies, followed by taking comments on them.

**f12. Does the Fed think it has fallen behind on rate cuts?** _(keyword recall 0.333, answered; judge: incorrect, not grounded, citations supported)_

> No, according to Chair Powell, the Fed has been very patient about reducing the policy rate [3]. They have waited for other central banks around the world to cut rates before doing so themselves. This patience has led to their confidence that inflation is moving sustainably under 2 percent.
>
> Note: There is no direct mention of whether the Fed thinks it has fallen behind on rate cuts in the provided context. The question asked if the Fed would have cut rates by 50 basis points if the market had been pricing in low odds of a 50-point move, implying that they may not have done so earlier, but this is not explicitly stated.

**f13. Does Powell see an elevated likelihood of a recession?** _(keyword recall 0.500, answered; judge: correct, grounded, citations supported)_

> No, according to Chair Powell, he doesn't see anything that suggests the likelihood of a recession is elevated [1].

**f14. Would the Fed have cut rates in July if it had seen the July employment report before that meeting?** _(keyword recall 1.000, answered; judge: 3 without a decision)_

> According to Chair Powell's statement, "if you ask if we'd gotten the July report before the meeting, would we have cut? We might well have." [1]
>
> So, based on this information, I can answer the question as follows:
>
> Yes, the Fed might have cut rates in July if it had seen the July employment report before that meeting.

**q21. How much funding did NIST allocate to develop the AI RMF?** _(unanswerable, abstained)_

> I don't know.
>
> The provided context does not mention any information about the amount of funding allocated by NIST for developing the AI RMF.

**q22. Which programming language does NIST recommend for building machine learning models?** _(unanswerable, abstained)_

> I don't know.
>
> [No relevant information provided in the given context]

**u01. How many organizations had adopted CSF 2.0 by the end of 2024?** _(unanswerable, abstained)_

> I don't know. The provided context does not contain information about the adoption rate or number of organizations that adopted the NIST Cybersecurity Framework (CSF) 2.0 by the end of 2024. [1][2]

**u02. What unemployment rate for Germany was discussed in the September 2024 press conference?** _(unanswerable, abstained)_

> I don't know.
>
> The provided context only discusses the US unemployment rate (3½ percent, then 4.2 percent) and does not mention Germany's unemployment rate at all. Therefore, I cannot provide an answer to this question based on the given context.
