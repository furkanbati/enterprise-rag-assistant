# Turkish Question Answering: Evaluation Report

Goal: answer Turkish questions about Turkish documents in Turkish, with sources, without making the English answers worse, and measure the result honestly.

## Summary

| Set | Before | After |
|---|---|---|
| Turkish dev, 20 questions: faithfulness | 0.844 | **0.923** |
| Turkish dev: answers in Turkish | 2/20 | **19/20** |
| Turkish dev: retrieval MRR | 0.778 | **1.000** |
| Turkish test, 12 questions: faithfulness | 0.674 | **0.805** |
| Turkish test: answers in Turkish | 4/12 | **11/12** |
| Turkish test: retrieval MRR | 0.675 | **0.900** |
| English NIST retrieval MRR (`hybrid_rrf_rerank`) | 1.000 | 1.000 |
| English RAGAS, 21 questions (`llama3`): faithfulness / answer relevancy | 0.934 / 0.939 | 0.977 / 0.953 |

- **Before:** `llama3` answers every question, reranked by the English `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **After:** Turkish questions are detected and routed to the multilingual reranker `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` and the chat model `qwen3.5:4b` with thinking turned off. English questions take the same route as before.
- **Largest effect:** the chat model. `llama3` answers most Turkish questions in English even when it has the right passages; `qwen3.5:4b` answers in Turkish and stays closer to the passages.
- **Largest retrieval effect:** the reranker. The English MiniLM pushed the right KVKK article out of the 3 passages given to the model; the multilingual one brings it to the top.
- **Still weak:** questions in everyday language whose words do not appear in the law (BM25 misses them, see t25), and reasoning slips of the 4B model (negations, mixed-up numbers).
- **English:** unchanged route, no regression. The "before" English RAGAS figures come from an earlier run on the CPU (2026-11-14), the "after" ones from the GPU (2026-11-22); the English route did not change in between, so the difference is run-to-run variation, not an improvement.

## Setup

| | |
|---|---|
| Frozen configuration | commit `ae428a6` on `feat/turkish-quality` |
| Documents | KVKK (Law No. 6698), NIST AI RMF 1.0, NIST CSF 2.0, FOMC press conference (18 September 2024), all in one index |
| Turkish sets | [`kvkk_tr_dev.jsonl`](../../datasets/kvkk_tr_dev.jsonl) (20 questions, 19 answerable) and [`kvkk_tr_test.jsonl`](../../datasets/kvkk_tr_test.jsonl) (12 questions, 10 answerable), each with a reference answer, page labels and evidence sentences |
| Retrieval | embeddings `nomic-embed-text`, sentence chunking with document titles, vector + BM25 with RRF (12 candidates each), cross-encoder reranking, 3 passages per answer |
| Judge | `gpt-6.1-sol`; answer relevancy embeddings `nomic-embed-text` and, separately, `bge-m3` |
| Hardware | Core Ultra 5 225H; models on the Arc 130T GPU through Ollama for Windows (`OLLAMA_HOST`), except where marked CPU |
| Dates | development set 2026-11-21, prompt trial 2026-11-22, test set 2026-11-23 |

Every change was decided on the development set. The test set was run once, with the frozen configuration, and nothing was changed afterwards.

"Evidence reached the model" counts the answerable questions for which a labelled evidence sentence is in one of the 3 passages. "Answers in Turkish" counts Turkish and English function words in the answer, which misses very short answers (for example t15, "Kurul üyelerinin görev süresi 4 yıldır.").

## Diagnosis (before any change)

On the 8 original Turkish questions:

- **Answer language:** with the same passages, `gpt-6-luna` answered 8/8 in Turkish and `llama3` 1/8.
- **Reranker:** the right article was in the 3 passages for 6/8 questions after hybrid retrieval but only 4/8 after the English reranker (t07 dropped from rank 1 to 11).
- **Embedding:** vector search alone placed the right article in the top 3 for 4/8 (t08 not in the top 50); BM25 placed it first for 5/8.
- **BM25 tokenizer:** `"KİŞİSEL".lower()` gives `ki̇şi̇sel` and splits into `ki | şi | sel`, a real bug for upper-case Turkish, but it changed little on these questions. Not changed.
- **Measurement:** the answer relevancy embedding `nomic-embed-text` scores Turkish lower (see below).

## Contribution of each change (development set)

### Reranker

| Turkish reranker | Hit@1 | Hit@3 | MRR | Evidence recall@3 | Time per query (CPU) |
|---|---|---|---|---|---|
| `ms-marco-MiniLM-L-6-v2` (English) | 0.737 | 0.789 | 0.778 | 0.658 | 1.5 s |
| `mmarco-mMiniLMv2-L12-H384-v1` | **1.000** | **1.000** | **1.000** | **0.921** | 2.5 s |

A screening on the 8 original questions also tried `BAAI/bge-reranker-v2-m3`: Hit@3 1.00 and MRR 0.875 (mmarco 0.938), but 12.8 s per query on the CPU against 2.4 s, so it was not adopted. Without any reranker, Hit@3 was 0.75 on those 8 questions.

### Chat model and reranker together

| Chat model + Turkish reranker | Evidence reached the model | Faithfulness | Answer relevancy (`nomic` / `bge-m3`) | Answers in Turkish |
|---|---|---|---|---|
| `llama3` + MiniLM (before) | 14/19 | 0.844 | 0.567 / 0.758 | 2/20 |
| `llama3` + mmarco | 19/19 | 0.863 | 0.584 / 0.757 | 4/20 |
| `qwen3.5:4b` + mmarco (after) | 19/19 | **0.923** | **0.864** / **0.882** | **19/20** |

The reranker alone fixes retrieval but barely changes the answers, because `llama3` still answers in English; the chat model is what makes the Turkish answers good.

### Thinking turned off (`OLLAMA_THINK_TR=false`)

`qwen3.5` reasons before answering by default. On the 8 original questions with thinking on, 8 of 24 answers came back empty: the reasoning filled the 4096-token context (9 generations stopped at 4095 tokens) and each answer took about two minutes. With thinking off, every answer arrived, in about 8 seconds on the GPU.

### Tried and not adopted: an answer-language rule in the prompt

"Answer in the language of the question, even when the context is in another language; this includes saying that you don't know":

| Set (chat model) | Prompt | Faithfulness | Answer relevancy (`nomic`) | Answers in Turkish | Time per answer |
|---|---|---|---|---|---|
| Turkish dev (`qwen3.5:4b`) | without the rule | 0.923 | 0.864 | 19/20 | 7.8 s |
| | with the rule | 0.893 | 0.902 | 18/20 | 8.8 s |
| English (`llama3`) | without the rule | 0.977 | 0.953 | – | 6.7 s |
| | with the rule | 0.971 | 0.933 | – | 10.8 s |

No measurable gain: the "not in the context" answer it targeted (t16) came out in English, per-question changes went both ways, and the English scores dipped slightly. The prompt was left unchanged.

### Not changed: the embedding model

The plan was to switch to a multilingual embedding (`bge-m3`) only if Turkish retrieval stayed below Hit@3 0.85 or MRR 0.75 after the reranker change. With the new reranker, the development set reached 1.000 for both and the test set 0.900, so the embedding was kept. The one test question retrieval missed (t25) is the case a multilingual embedding should help with.

## Measurement correction, kept apart from the system

Answer relevancy compares the question with questions generated from the answer through an embedding. `nomic-embed-text` is mostly English, so it scores a Turkish question against Turkish answers lower, and against English answers much lower. Re-scoring the same answers with the multilingual `bge-m3` changes only the measurement:

| Answers | `nomic-embed-text` | `bge-m3` | Change |
|---|---|---|---|
| Original 8 Turkish questions, `llama3`, `hybrid_rerank` (2026-11-14) | 0.565 | 0.715 | +0.150 |
| Dev, `llama3` + MiniLM | 0.567 | 0.758 | +0.191 |
| Dev, `qwen3.5:4b` + mmarco | 0.864 | 0.882 | +0.018 |
| Test, `llama3` + MiniLM | 0.528 | 0.572 | +0.044 |
| Test, `qwen3.5:4b` + mmarco | 0.740 | 0.733 | −0.007 |
| Original 21 English questions, `llama3`, `hybrid_rerank` (2026-11-14) | 0.939 | 0.927 | −0.012 |

- The correction raises the English answers to Turkish questions most (`llama3`). `bge-m3` does not penalize an answer in the wrong language at all, so on its own it would hide the language problem. That is why the share of answers in the question's language is reported separately.
- For `qwen3.5:4b`, which answers in Turkish, the two embeddings agree within 0.02, so its gain over `llama3` is a system improvement, not a measurement effect.

## Test set (run once)

| | Before: `llama3` + MiniLM | After: `qwen3.5:4b` + mmarco |
|---|---|---|
| Retrieval Hit@1 / Hit@3 / MRR | 0.600 / 0.700 / 0.675 | **0.900 / 0.900 / 0.900** |
| Evidence recall@3 | 0.700 | **0.900** |
| Evidence reached the model | 7/10 | **9/10** |
| Faithfulness | 0.674 | **0.805** |
| Answer relevancy (`nomic` / `bge-m3`) | 0.528 / 0.572 | **0.740 / 0.733** |
| Answers in Turkish | 4/12 | **11/12** (the 12th, t27, is Turkish but too short to count) |
| Time per answer (GPU) | 9.7 s | 9.9 s |

The scores are lower than on the development set (faithfulness 0.805 against 0.923), as expected when every choice was made on the development set. With 12 questions, one question moves an average by about 0.08, so the exact figures are uncertain; the direction and size of the improvement are consistent across both sets.

## Remaining errors

1. **Everyday wording, retrieval miss (test t25).** "Bir şirket kişisel verilerimi benim iznim olmadan başka bir şirkete verebilir mi?" The law says "aktarılamaz"; no question word matches, so BM25 does not find the article, vector search puts it third, and after fusion it is out of the candidates the reranker sees. The answer ("Hayır, … açık rızanız olmaksızın …") goes in the right direction without support in the passages (faithfulness 0.25). A multilingual embedding is the next step for this kind of question.
2. **Misread deadline (test t23).** "Kuralların tam tersidir: Kurul bir şikâyet üzerine 60 günden fazla cevap ver…" The passage says the request counts as rejected if there is no answer within 60 days; the model inverts the rule (faithfulness 0.50).
3. **Contradiction in one sentence (test t32).** "Hayır, kurul toplantılarındaki görüşmeler herkese açıktır; aksine bu görüşmeler …" The model starts with the wrong statement and then corrects itself (faithfulness 0.50).
4. **Swapped numbers (dev t07, prompt trial).** "9 üyeden oluşur; bunlardan 5'i Cumhurbaşkanı, 4'ü ise Türkiye Büyük Millet Meclisi…" The law says the opposite (5 by the Grand National Assembly, 4 by the President). This appeared in one run and not in another with the same passages.
5. **Unanswerable questions with extra guesses (test t30, t31).** The model now says in Turkish that the context does not cover cookies or a GDPR comparison, but adds speculation around it (faithfulness 0.67 and 0.89).

Errors 2–4 are reasoning slips of a 4B model; a larger model (for example `qwen3.5:9b`) may reduce them, at a cost in speed.

## Speed

Time per answer on a Core Ultra 5 225H:

| Model | CPU (Docker, default setup) | Arc 130T GPU (Ollama for Windows) |
|---|---|---|
| `llama3` | about 90 s | about 8 s |
| `qwen3.5:4b` | about 220 s | about 8 s |

`qwen3.5:4b` generates text more slowly than `llama3` on a CPU (about 0.34 tokens per second in Docker), so Turkish answers in the default CPU setup take three to four minutes. The README describes the optional GPU setup.

## Reproducing

The documents are downloaded as described in the [dataset README](../../datasets/README.md). The GPU runs set `OLLAMA_HOST=http://host.docker.internal:11434`; without it the same commands run on the CPU in Docker.

```bash
# Retrieval (Hit@k, MRR, evidence recall); add --rerank-model-tr cross-encoder/ms-marco-MiniLM-L-6-v2 for "before"
docker compose run --rm eval python -m evaluation --dataset evaluation/datasets/kvkk_tr_dev.jsonl

# Answers, scored by the judge; for "before" add -e CHAT_MODEL_TR=llama3 to the docker command and the MiniLM reranker as above
docker compose run --rm eval python -m evaluation.ragas_eval --config hybrid_rerank --dataset evaluation/datasets/kvkk_tr_dev.jsonl --metrics faithfulness answer_relevancy

# Answer relevancy with bge-m3: blank answer_relevancy in a copy of the results, then
docker compose run --rm -e RAGAS_EMBED_PROVIDER=ollama -e RAGAS_EMBED_MODEL=bge-m3 eval python -m evaluation.ragas_eval --config hybrid_rerank --rescore --output <copy>
```

Replace `kvkk_tr_dev.jsonl` with `kvkk_tr_test.jsonl` for the test set.

## Result files

| Folder | Contents |
|---|---|
| [`dev/retrieval/`](dev/retrieval) | Retrieval reports on the development set, MiniLM and mmarco |
| [`dev/ragas/`](dev/ragas), [`dev/ragas_bge_m3/`](dev/ragas_bge_m3) | Answers and scores on the development set, with `nomic-embed-text` and `bge-m3` answer relevancy |
| [`test/`](test) | The same for the test set |
| [`prompt_trial/`](prompt_trial) | Runs with the answer-language rule that was not adopted |
| [`english/`](english) | English RAGAS (21 questions) and NIST retrieval with the final configuration |
