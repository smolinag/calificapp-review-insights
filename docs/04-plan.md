# 4. Plan

Each phase ends with a commit, so the history shows the order of the work.

| Phase | Goal | Output | Checklist item it serves |
|---|---|---|---|
| 0. Define | Problem, data provenance, spec, plan, tasks | `docs/01–05`, flow diagram | Define; spec-first commit history |
| 1. Data | Owner permission, anonymized dataset, test company excluded, manual PII review, synthetic hard cases, gold labels | `data/reviews_anon.json`, `data/synthetic.json`, `data/labels_gold.csv`, labeling notes | Data provenance; data that stresses the solution |
| 2. Baseline without context | Classifier and ingest generated **without** `CLAUDE.md`; first metrics | Saved outputs in `evidence/before/` | Context artifact "before" |
| 3. Context artifact | Write `CLAUDE.md`, regenerate, compare | `CLAUDE.md`, `evidence/after/`, comparison note | Context artifact before/after |
| 4. Retrieval + Q&A | Embeddings, Chroma, router, SQL stats, answer + citation verification, Streamlit | Working Q&A end to end | Retrieval pipeline; working prototype |
| 5. Digest | Weekly digest HTML | Digest for the last week of real data | Working prototype |
| 6. Evaluate | Run S1–S7; full-context (A) vs retrieval (B) | `evidence/eval_results.md` | Measured improvement |
| 7. Break it | Look for failures, fix one, re-measure | `docs/failure-analysis.md` | Failure analysis; measured improvement |
| 8. Review | Review AI-generated code across intent, tests, security, performance, maintainability; record at least one error caught | `docs/ai-review.md` | AI output review |
| 9. Communicate | One pitch slide, demo recording/transcript including a bad case, effort statement | `docs/pitch`, `docs/demo.md`, `docs/effort.md` | Communicate |

## Risks

| Risk | Mitigation |
|---|---|
| Owner does not give permission | Switch to fully synthetic data calibrated on the aggregate statistics already recorded in the provenance note (no records copied) |
| Too few real negatives to measure recall meaningfully | Synthetic hard cases, reported separately; recall reported with absolute counts (e.g., "12/12"), not just percentages |
| Local model misses hard cases | Expected: reported in the failure analysis. If a Claude key or Portkey access becomes available, the same evaluation is rerun with Claude for comparison |
| Full-context baseline does not fit in the local model's context | Reported as a finding (it supports retrieval); measured at the largest context that fits |
| Time | Cut order if needed: digest polish → Streamlit (CLI is enough) → router LLM fallback |
