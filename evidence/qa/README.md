# Q&A: effect of the relevance filter

Same 25 questions, same retrieval, same local model (`qwen2.5:7b`). The only change: before answering, each of the 20 retrieved reviews is checked on its own ("¿sirve para responder la pregunta?"), and only those judged relevant reach the answer step.

| | Without filter (`qa_v1.md`) | With filter (`qa_v2_relevance_filter.md`) |
|---|---|---|
| **Correct** | **13/25** (12/25 in an earlier identical run) | **15/25** |
| Counting questions | 8/8 | 8/8 |
| Meaning questions | 5/17 | 7/17 |
| Invalid citations | 0 | 0 |
| Model calls per meaning question | 2 | up to 22 |

**Run-to-run variation.** Two runs of the same no-filter configuration scored 12/25 and 13/25: the local model is not fully deterministic even at temperature 0. The filter's gain is therefore about **+2 questions**, which is small relative to that noise. A firmer claim would need several runs per configuration.

**Latency** was measured on different runs with the GPU in different states (warm/cold), so the medians in the two files are not comparable. What is certain: with the filter each meaning question makes up to 20 extra model calls (~0.5–0.8 s each).

## Per question (only those not correct in both)

| Q | Without filter | With filter | Change |
|---|---|---|---|
| Q11 unresolved warranty claims | 0/1 | 1/1 | fixed |
| Q17 WhatsApp / virtual | 1/2 | 2/2 | fixed |
| Q10 inappropriate conduct | 0/2 | 1/2 | better (still misses R00309) |
| Q12 price complaints | 0/2 | 1/2 | better |
| Q18 good rating with a complaint | 0/3 | 1/3 | better |
| Q23 installation and workshop | 0/2 | 1/2 | better |
| Q16 coffee and drinks | 2/3 | 0/3 | **worse** |
| Q22 rude service | 2/3 | 1/3 | **worse** |
| Q14 recognitions | 2/5 | 1/5 | **worse** |
| Q13 asked to be called | 0/1 | 0/1 | no change |
| Q15 "chicas del segundo piso" | 0/1 | 0/1 | no change |
| Q25 count + list price complaints | wrong list | wrong list | no change (classifier theme error, not Q&A) |

## Why it got worse where it did

- **Q16** ("café y bebidas"): the filter rejected all 3 reviews, which the unfiltered answer had partly found. Likely cause: the filter rule "generic praise is not relevant to questions about concrete topics" applied to "Tienen excelente atención y muy buen café", a compliment that does mention the topic. The rule is too blunt.
- **Q14** (recognitions), **Q22** (rude service): the filter dropped reviews that were needed; same pattern of over-rejecting.

## Still failing in both

- **Q15**: the review says "chicas de arriba"; neither path connects "arriba" with "segundo piso".
- **Q13**: "Por favor llamen si la consiguen" is not recognised as "asked to be called".
- **R00309** ("Pero muy morbosa") is missing from every misconduct answer: the classifier never flagged it, so labeled retrieval does not prioritise it.

# Router: complaint and request words decide `problems` by rule

**Failure.** Q13 ("¿Algún cliente pidió que lo llamáramos?") was routed `general` by the model, although its system prompt lists "customers asking for something" under `problems`. Plain retrieval never surfaced R01215 ("Por favor llamen si la consiguen"), which the classifier *had* flagged as `review`. H15 ("¿Hay quejas sobre el parqueadero?") was also routed `general` despite "quejas".

**Change** (`src/review_insights/router.py`): one word list (`PROBLEM_WORDS`: queja, reclamo, mal, grosero, acoso, incómodo, accidente, garantía, no supo, llamáramos/llamen…) sends a question to `problems` before the model is asked; the model only decides questions no rule covers. The same list gates the `actionable` filter, which had its own shorter copy. Unit tests: `tests/test_router.py` (stubbed model, newly written questions).

**Also caught while writing the tests:** "¿Qué empleado tuvo **menos** reseñas?" matched the counting rule, but `stats` always sorted descending, so it would have named the employee with the *most* reviews. Added `bottom_employee` / `bottom_month` (`tests/test_stats.py`).

| | Before (`../improvement/qa_dev_after.md`, `../improvement/qa_heldout_after.md`) | After (`qa_v3_router_rules.md`, `heldout_v3_router_rules.md`) |
|---|---|---|
| Routes changed (of 40 questions) | — | 2 (Q13, H15 → problems) |
| Dev questions correct | 14/25 | 15/25 |
| Held-out questions correct | 10/15 | 10/15 |
| Invalid citations | 0 | 0 |

Per question, dev set:

| Q | Route changed? | Before | After |
|---|---|---|---|
| Q13 asked to be called | yes | 0/1 | **1/1** (fixed by the route) |
| H15 parking complaints | yes | OK (none) | OK (none) |
| Q18 good rating with a complaint | no | 1/3 | 2/3 |
| Q21 waiting-time complaints | no | cited a review when none apply | OK |
| Q17 WhatsApp / virtual | no | 2/2 | **1/2** |

Only Q13 can be attributed to the change. Q17, Q18 and Q21 kept the same route and filters, so their movement is the run-to-run variation described above (12–13/25 between identical runs); net, the change is worth about one question.

**What it does not fix, or makes worse**
- Word lists miss paraphrases: "¿Alguien quedó descontento?" has no listed word and still depends on the model.
- Positive questions with a listed word go to labeled retrieval, which spends half its slots on flagged complaints: "¿Algún cliente agradeció la garantía?" now routes `problems`.
- H08 ("¿Algún empleado le arregló algo a un cliente?") is still routed `problems` by the model, though it asks about praise.
- Q25 is unchanged: routing is right (counting), the wrong list comes from classifier themes (R00933 "precios altos" labeled `otro`, R02123 sizing complaint labeled `precio`).
