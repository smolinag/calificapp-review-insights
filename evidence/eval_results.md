# Results against the definition of success (S1–S7)

Criteria and targets from `docs/01-problem-statement.md`. Model: local `qwen2.5:7b` via Ollama, temperature 0. Classifier run `v2` (prompt v1 + alert words). Q&A after the router fix (commit `b60fc4e`). Real and synthetic results are reported separately, as counts.

## Summary

| # | Criterion | Target | Result | Met? |
|---|---|---|---|---|
| S1 | Urgent recall | 100% | Real **4/4** · held-out **8/8** · synthetic **15/17** | Real and held-out yes; synthetic no |
| S2 | Actionable recall | ≥ 90% | Real **14/14** · held-out **12/12** · synthetic **29/32** (91%) | Yes |
| S3 | Actionable precision | ≥ 60% | Real **14/14** · held-out **12/15** (80%) · synthetic **29/30** | Yes |
| S4 | Invalid citations | 0 | **0** in 40 Q&A answers (and in every earlier run) | Yes, with a caveat |
| S5 | Q&A correct | ≥ 80% | Dev **15/25** (60%) · held-out **10/15** (67%) | **No** |
| S6 | Counting questions exact | 100% | Dev **8/8** · held-out **5/5** | On the set yes; not robust |
| S7 | Retrieval vs full context: cost and latency | Measured | See below | Measured |

## Data behind each number

| Set | What it is | n | Actionable (gold) | Urgent (gold) |
|---|---|---|---|---|
| Real | Every real comment, Oct 2025–Oct 2026, hand-labeled (`data/labels_gold.csv`) | 997 | 14 | 4 |
| Synthetic | Hard cases written before the classifier (`data/synthetic_cases.csv`) | 44 | 32 | 17 |
| Held-out | Written and committed (`5f20081`) before the alert words were tuned (`data/heldout_cases.csv`) | 16 | 12 | 8 |
| Demo | 45 invented complaints for the demo, written after the classifier by the same author (`data/demo_negative_cases.csv`) | 45 | 45 | 21 |
| Questions, dev | `eval/questions.json`: 8 counting, 16 meaning, 1 hybrid | 25 | | |
| Questions, held-out | `eval/questions_heldout.json`: 5 counting, 10 meaning | 15 | | |

The real set is small where it matters: only 4 urgent and 14 actionable reviews. "4/4" is the honest result, but one more miss would be 75%. The synthetic and held-out sets exist to stress the classifier beyond those 14. All synthetic, held-out and demo cases were written by the same person who built the classifier (with Claude), which limits how independent they are (`docs/02-data-provenance.md`).

## S1–S3: classifier

Source: `evidence/improvement/classifier_v2_alerts.md`. Progression from the bare prompt to the current run:

| | v0 (no context) | v1 (`CLAUDE.md`) | v2 (+ alert words) |
|---|---|---|---|
| S1 real | 2/4 | 3/4 | **4/4** |
| S1 synthetic | 7/17 | 14/17 | **15/17** |
| S1 held-out | — | 6/8 | **8/8** |
| S2 real | 8/14 | 13/14 | **14/14** |
| S3 real | 8/33 | 13/13 | **14/14** |
| S3 held-out | — | 11/12 | **12/15** |

Demo set (not independent evidence): S1 20/21, S2 44/45, S3 44/44.

Urgent reviews still missed: S0027 (refused exchange, misspelled), S0038 (salesperson asked if the customer has a boyfriend), D0039 (sarcastic report of a fitted mirror falling off). Details: `docs/failure-analysis.md` F01–F03.

Cost: ~0.8 s per comment on the local GPU (median 797 ms, p90 1057 ms), 14 minutes for all 1,102 comments, no per-call fee.

## S4: grounding

Every citation in the 40 answers points to a review the model was given, and that holds in every Q&A run in `evidence/qa/` and `evidence/improvement/`. The check (`answer.verify`) also rejects malformed IDs.

**Caveat.** S4 measures provenance, not support. Q15 cites R00309, which does not mention the second floor, and Q13 cites R03023 as a call request when it is not (failure analysis F10, F13). Both pass S4. A stricter check would ask whether each cited review supports its sentence; it is not built.

## S5: question answering

Sources: `evidence/qa/qa_v3_router_rules.md`, `evidence/qa/heldout_v3_router_rules.md`.

| | Dev | Held-out |
|---|---|---|
| Counting | 8/8 | 5/5 |
| Meaning | **7/16** | **5/10** |
| Hybrid (count + list) | 0/1 | — |
| **Total** | **15/25** | **10/15** |

S5 is not met, and meaning questions are the reason: about half are answered correctly. A meaning answer counts only if it cites every required review; extra wrong citations are not penalised (F14), so these numbers are an upper bound.

Run-to-run variation is about ±1 question on the dev set (12/25 and 13/25 in two identical runs, `evidence/qa/README.md`), so differences of one question between configurations are not evidence.

What was tried, measured on both sets: per-review relevance filter (+2 dev), labeled retrieval for problem questions (recall 21/31 → 25/31), classifier label shown to the model (no change), router rules (+1 dev, Q13). Where the remaining misses come from: the right review is usually retrieved and then dropped by the 7B model at the relevance or answer step (F08, F09, F12, F15); a minority are retrieval misses on generic praise (F11).

## S6: counting

13/13 counting questions in the two sets are exact, because the number comes from fixed SQL (`stats.py`), not the model.

**Not robust.** Outside the set, questions an owner would naturally ask return a wrong number with no warning: "¿Cuántas reseñas hubo en septiembre?" (no year) answers 3184 instead of 274, "la semana pasada" answers 3184, and "EMP 15" with a space returns the store-wide average (F17–F19). The SQL is exact; the filter extraction in front of it is not.

## S7: retrieval vs full context

Source: `evidence/eval_fullcontext.md` (`scripts/eval_fullcontext.py`). The 26 meaning questions of both sets, asked two ways in the same session: **A** sends all 997 real comments in one prompt (~18,000 input tokens, fits the 32k context set for it); **B** is the normal pipeline (router, top-20 retrieval, per-review relevance check, answer).

| | A: full context | B: retrieval |
|---|---|---|
| Correct, dev meaning | **1/16** | **7/16** |
| Correct, held-out meaning | **1/10** | **6/10** |
| Model calls per question | 1 | 21–22 |
| Input tokens per question (median, all calls) | 17,987 | 5,629 |
| Invalid citations | **13** | 0 |
| Latency per question | ~24–33 s | ~4 s in normal use (see note) |
| Money cost | none (local GPU) | none (local GPU) |

Full context is worse on every count for this model. Both questions A got right are ones whose correct answer is "none" (Q21, H15). It found neither the accident (R01972) nor the harassment report (R01301), and it cited 13 IDs that do not exist in the data. With 997 near-identical compliments in one prompt, the 7B model does not find the few reviews that matter: the same "needle among compliments" problem the project addresses for the owner.

**Latency note.** In this run B measured a median of 28 s, against 3.8–4.1 s in the normal Q&A runs (`evidence/qa/qa_v3_router_rules.md`). Alternating A (32k context) and B (8k context) makes Ollama reload the model at each switch, so B paid a reload on every question. The A figure (33 s median here, 24 s in a single warm call) is the more reliable of the two in this file.

**Where retrieval is worse.** B spends ~3× fewer input tokens but makes 22 calls instead of 1, so with a paid API it would pay 22 per-request overheads per question. And B cannot see reviews it does not retrieve (F11). A larger model with a long context might reverse this result. That comparison (Claude on the same questions) was not run.

## What these results mean for the owner

- **Finding what to act on works** on the real data: all 14 actionable reviews, including the 4 urgent ones, are flagged, with no false alarms (14/14 precision). This is the core problem in `docs/01-problem-statement.md`.
- **Counting works** when the question names a full month and year, an exact pseudonym or a star rating.
- **Open questions are unreliable**: about half the meaning questions miss a review that should be cited. The owner should treat "No encontré reseñas sobre eso" as "not found", not as "there are none".
