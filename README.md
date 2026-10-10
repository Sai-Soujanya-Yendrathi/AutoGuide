# AutoGuide AI — Full MSAI 633 RAG Project

This repository implements the **proposed architecture**, with the approved enterprise-style Streamlit dashboard and bundled five automotive images. The code is supplied as a reproducible implementation, **not evidence that the required 150+ pages, PDFs, tables, golden questions or performance outcomes have already been achieved**. These must be collected, verified and reported by the project team.

## Run the UI immediately (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m streamlit run app.py
```

Demo mode (`AUTOGUIDE_DEMO=1`) works without network or an API key once dependencies are installed. It displays **mock documents only**, not real NHTSA-grounded answers.

## Produce real indexed data

1. Replace the placeholder contact with a real team email and manually verify NHTSA crawl permissions, seed pages and terms of use. Robot failures are treated as block/skip, not bypassed.
2. Run `python -m pipeline.ingest --email team@example.edu --max-pages 180` (default 1-second request spacing). Inspect `data/crawl_log.json` and `data/documents.jsonl`.
3. Run `python -m pipeline.validate`. Compare observed counts with required: **150 HTML pages, 5 PDFs, 3 pages containing tables**; proposal target 180/10/5. The project DOES NOT automatically ensure minimums are met.
4. Run `python -m pipeline.indexing --strategy both` to persist fixed (~500 words approximate, 100-word overlap) and heading-aware chunks, embeddings (all-MiniLM-L6-v2, normalized 384d), and Chroma databases. Note word chunking approximates, but does not exactly equal, the proposal's 500 tokens. A tokenizer would be needed for exact token-based compliance.
5. Fill `data/golden_set.json` with **40 human-verified** records, using `data/golden_template.csv` as a field guide (15 single-hop, 6 multi-hop, 4 comparative, 4 temporal, 8 unanswerable, 3 ambiguous/adversarial). Record evidence quotes <=25 words and source URLs. Stratify **24 dev / 16 test**.
6. Execute `python -m pipeline.evaluate --split dev` during tuning, and `python -m pipeline.evaluate --split test` **only once after freezing parameters**. Evaluator reports B1/B2/B3 *retrieval only* and depends on verified relevant chunk IDs. B0, generation correctness, refusal rates, 95% bootstrap / McNemar and costs **need separate human-verified test execution**; do not report them as automatically measured.
7. Configure `.env`: `AUTOGUIDE_DEMO=0`, `OPENAI_API_KEY=...`, `OPENAI_MODEL=gpt-4o-mini`. Run `python -m streamlit run app.py`.

## Major components

| Pipeline | Code | State |
|---|---|---|
| Scrape / HTML + PDF + tables | `pipeline/ingest.py` | Runnable, requires live accessible allowed NHTSA pages |
| Clean metadata + store raw snapshots | `pipeline/ingest.py` | Implemented |
| Fixed / heading-based chunking | `pipeline/indexing.py` | Implemented (word-count proxy) |
| Embeddings, Chroma vectors and replacement | `pipeline/indexing.py` | Implemented (not atomic index swap) |
| BM25 + dense + RRF hybrid | `pipeline/retrieval.py` | Implemented |
| Cross-encoder reranking (20 -> 5) | `pipeline/retrieval.py` | Implemented |
| Grounded GPT-4o-mini, NHTSA citations and refusal | `chatbot.py` | Implemented, automated checks not a safety guarantee |
| Streamlit enterprise dashboard, history & inspector | `app.py`, `assets/` | Implemented |
| Golden set & retrieval analysis | `pipeline/evaluate.py` | Metrics on externally verified golden data |
| 8 markdown reports | `reports/` | Templates awaiting measured results |

## Honest constraints and safety

- The dataset is **not included** because unverified crawling and invented NHTSA quotes would not meet the project's requirements.
- The original proposal demands **exact 500-token chunks**, 95% confidence or McNemar, 15 categorized failures, and multiple runtime ethics safeguards. This implementation has a starting point, but those items still require finishing and measuring.
- The crawler follows `robots.txt`, uses a team contact and request throttling; the current script retains all raw bytes. Avoid collecting PII and review accidental sensitive content before indexing.
- URLs are NHTSA-only for citation and no demo sources are reported as verified.
- Untrusted retrieval data is explicitly labeled in prompts; this reduces, but does not remove, prompt-injection risks.
- No secrets should be committed; `.env` is ignored by Git.
- For recall status of an individual VIN, direct users to current official verification instead of relying on potentially stale indexed documents.

## Run checks

`python -m pytest -q`

## Proposal division of work

Members 1–7: PM, collection, extraction, chunking + vector store, retrieval/reranking, chatbot developer (Soujanya), evaluation lead. Your chatbot UI and GPT integration are in `app.py` / `chatbot.py`, but everyone should coordinate integration and tests.
