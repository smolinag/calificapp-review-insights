# 5. Tasks

Status: `[ ]` to do · `[x]` done. Each task lists its acceptance criterion.

## Phase 1 — Data
- [ ] **T01** Get the store owner's permission to use anonymized reviews. *Done when:* written confirmation saved (outside the repo) and referenced in the provenance note.
- [ ] **T02** Ingest script: raw export → anonymized JSON, test company excluded. *Done when:* output has no `raterName`/`raterPhone`, no real employee/company/device names; unit test covers name replacement inside comments.
- [ ] **T03** Manual PII review of every comment. *Done when:* each comment checked; fixes and count recorded in the provenance note.
- [ ] **T04** Write synthetic hard cases (≥ 40, all categories in the provenance note). *Done when:* stored with `synthetic = 1`.
- [ ] **T05** Gold labels for all real comments + synthetic. *Done when:* `labels_gold.csv` complete; ambiguous cases listed in labeling notes.
- [ ] **T06** Evaluation questions (~25) with answer keys, counting and meaning mixed. *Done when:* `eval/questions.yaml` written.

## Phase 2 — Baseline without context
- [ ] **T07** Project skeleton (`pyproject`, `.env.example`, SQLite loader). *Done when:* `reviews.db` loads from the anonymized JSON.
- [ ] **T08** Classifier v0 generated without `CLAUDE.md`. *Done when:* runs on the full set; outputs and generated code saved in `evidence/before/`.
- [ ] **T09** Metrics script for S1–S3. *Done when:* prints recall/precision with absolute counts, real vs synthetic.

## Phase 3 — Context artifact
- [ ] **T10** Write `CLAUDE.md`. *Done when:* covers glossary, taxonomy, anonymization, prompt-injection rule, conventions, tests.
- [ ] **T11** Regenerate classifier with `CLAUDE.md`; compare. *Done when:* `evidence/after/` plus a comparison note with numbers.

## Phase 4 — Retrieval + Q&A
- [ ] **T12** Embeddings + Chroma index. *Done when:* "¿Algún cliente tuvo un accidente?" returns R01972 in the top 20.
- [ ] **T13** Router + SQL stats. *Done when:* unit tests for ≥ 10 counting and meaning questions pass.
- [ ] **T14** Answer with citations + verification. *Done when:* invalid citation in a crafted response is detected by a test.
- [ ] **T15** Portkey integration (or local token logging). *Done when:* cost and latency recorded per call.
- [ ] **T16** Streamlit UI. *Done when:* ask a question, see answer, open cited review.

## Phase 5 — Digest
- [ ] **T17** Weekly digest HTML. *Done when:* generated for the last week of real data; every claim has a verified citation.

## Phase 6 — Evaluate
- [ ] **T18** Full-context baseline (A) vs retrieval (B) on the evaluation questions. *Done when:* accuracy, cost and latency table for both.
- [ ] **T19** Compute S1–S7. *Done when:* `evidence/eval_results.md` with numbers and inputs.

## Phase 7 — Break it
- [ ] **T20** Failure hunt: ≥ 8 specific failing inputs with cause. *Done when:* `docs/failure-analysis.md`.
- [ ] **T21** Fix one failure, re-measure, report what got worse. *Done when:* before/after numbers recorded.

## Phase 8 — Review
- [ ] **T22** AI output review (intent, tests, security, performance, maintainability), ≥ 1 error caught and corrected. *Done when:* `docs/ai-review.md`.

## Phase 9 — Communicate
- [ ] **T23** One pitch slide for the store owner.
- [ ] **T24** Demo recording or transcript, including at least one bad case.
- [ ] **T25** Declared-effort statement: hours and what was cut.
