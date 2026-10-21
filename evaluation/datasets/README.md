# Evaluation Datasets

Each file is JSON Lines: one labelled question per line. See `EvalSample` in [`../dataset.py`](../dataset.py) for the fields.

| Dataset | Questions | Documents | Purpose |
|---|---|---|---|
| [`nist_ai_rmf.jsonl`](nist_ai_rmf.jsonl) | 22 (20 answerable) | NIST AI RMF 1.0 | Regression baseline for retrieval and answers, labelled at page level |
| [`chunking_benchmark.jsonl`](chunking_benchmark.jsonl) | 52 (48 answerable) | NIST AI RMF 1.0, NIST CSF 2.0, FOMC press conference | Comparing chunking strategies across documents with different structure |

## Chunking benchmark

The benchmark combines three documents with different structure:

- **NIST AI RMF 1.0**: a structured framework with clear headings. The questions are the 20 answerable questions of `nist_ai_rmf.jsonl`.
- **NIST CSF 2.0**: another NIST framework with overlapping vocabulary (a GOVERN Function, Profiles, Tiers). Several questions use terms that also appear in the AI RMF, so retrieval has to pick the right document.
- **FOMC press conference transcript (18 September 2024)**: a question-and-answer transcript without headings, where topics change often. Docling finds no sections in it, so every chunk gets page 1.

Every answerable question has a `source` and `evidence`: sentences, copied verbatim from the Docling output, that contain the answer. Evidence recall is the metric that reacts to chunking. Page-level metrics cannot, because all chunks of a section share the page where the section starts, and in the FOMC transcript every chunk is on page 1.

When evidence is not found in any indexed chunk, the report lists it under "Missing Evidence". This usually means the document was parsed differently from when the labels were made.

### Documents

The documents are U.S. government works in the public domain. PDFs are not committed; download them into the repository root:

```bash
curl -o nist.ai.100-1.pdf https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
curl -o NIST.CSWP.29.pdf https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf
curl -o FOMCpresconf20240918.pdf https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20240918.pdf
```

Upload all three through `POST /upload`, then run:

```bash
docker compose exec api python -m evaluation \
    --dataset evaluation/datasets/chunking_benchmark.jsonl \
    --output evaluation/results/chunking_benchmark
```
