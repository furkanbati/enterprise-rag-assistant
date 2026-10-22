# Chunking Strategy Comparison

Measured on 2026-10-22 with the [chunking benchmark](../../datasets/README.md#chunking-benchmark) (52 questions, 48 answerable, over the NIST AI RMF, NIST CSF 2.0 and an FOMC press conference transcript), `ollama/nomic-embed-text` embeddings and the `hybrid_rrf_rerank` retrieval strategy. Each variant was ingested into its own collection. The full `sentence` report is in [`report.md`](report.md).

## Variants

| Variant | Chunks (AI RMF / CSF / FOMC) | Median chunk chars | Ingest time in s (AI RMF / CSF / FOMC) |
|---|---|---|---|
| `sentence` (min 300, max 1000) | 221 / 124 / 132 | ~400 | 67 / 46 / 40 |
| `semantic-p80-w1` | 138 / 86 / 78 | 512–682 | 118 / 70 / 79 |
| `semantic-p90-w1` | 127 / 82 / 73 | 638–809 | 118 / 72 / 80 |
| `semantic-p95-w1` | 115 / 81 / 67 | 639–869 | 118 / 88 / 79 |

The semantic variants embed a window of ±1 sentence around every sentence and split where the distance between consecutive windows is above the given percentile of all distances in the document. Segments shorter than 300 characters are merged and segments longer than 1000 are split into balanced parts.

## Evidence recall at k = 3

| Variant | Evidence@3 | Context chars@3 |
|---|---|---|
| `sentence` | **0.878** | **1247** |
| `semantic-p80-w1` | 0.865 | 2121 |
| `semantic-p90-w1` | 0.854 | 2248 |
| `semantic-p95-w1` | 0.844 | 2420 |

## Evidence recall at equal context budgets

Larger chunks raise recall at a fixed k simply by sending more text. For each question, this table takes the retrieved chunks that fit within a character budget and measures the evidence they contain. Budgets below 1200 characters are left out, because a single semantic chunk does not fit in them; budgets above 3000 are left out, because the `sentence` run stops at k = 8 (about 3300 characters).

| Budget (chars) | 1200 | 1600 | 2000 | 2500 | 3000 |
|---|---|---|---|---|---|
| `sentence` | **0.854** | **0.878** | **0.896** | **0.907** | **0.921** |
| `semantic-p80-w1` | 0.760 | 0.781 | 0.781 | 0.890 | 0.900 |
| `semantic-p90-w1` | 0.781 | 0.812 | 0.854 | 0.865 | 0.900 |
| `semantic-p95-w1` | 0.677 | 0.719 | 0.760 | 0.802 | 0.879 |

By source, at 1600 characters:

| Variant | AI RMF | CSF 2.0 | FOMC transcript |
|---|---|---|---|
| `sentence` | **1.000** | **0.743** | 0.839 |
| `semantic-p90-w1` | 0.900 | 0.643 | **0.857** |

## Findings

- At every budget, sentence-aligned chunks retrieve more evidence than semantic chunks. Vector search alone loses more (0.726 vs 0.59–0.64 at 1200 characters): embeddings of larger chunks are less specific.
- In documents with clear headings, Docling's sections already follow topic boundaries, so semantic splitting adds size rather than better boundaries.
- In the FOMC transcript, which has no headings, `semantic-p90-w1` is 0.02–0.07 ahead at 1200–2500 characters. This rests on 14 questions, so it is a lead to follow, not a result.
- `sentence` stays the default. The semantic chunker is available with `CHUNKING_STRATEGY=semantic`.

## Limitations

- 48 answerable questions: one question moves an average by about 0.02.
- One embedding model; the semantic breakpoints may differ with a stronger model.
- A CSF appendix list without sentence punctuation becomes one 5,819-character chunk in both strategies, because chunks never split a sentence.

## Reproducing

With the three PDFs in the repository root (see the [dataset README](../../datasets/README.md#documents)), set the chunking settings in `.env`, restart the API, upload the PDFs through `POST /upload`, and run the benchmark with the same settings:

```dotenv
CHUNKING_STRATEGY=semantic
SEMANTIC_PERCENTILE=90
```

```bash
docker compose exec api python -m evaluation \
    --dataset evaluation/datasets/chunking_benchmark.jsonl \
    --ks 1 2 3 4 5 6 8 \
    --output evaluation/results/chunking_benchmark/semantic-p90-w1
```

Each chunking configuration has its own collection, so switching settings never mixes chunks of different variants.
