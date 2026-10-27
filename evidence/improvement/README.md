# Measured improvement: alert-word safety net

## The failure

R00309, a real review: *"Excelente servicio. Pero muy morbosa"* (5★). A report of lewd behaviour by staff, hidden in a top rating. The classifier missed it without context (v0: `normal`) and with the full CLAUDE.md context (v1: `normal`, reason: "Comentario sexual no relacionado con el servicio"). Because the classifier missed it, labeled retrieval never prioritised it, and no answer about misconduct ever cited it.

## The change

`src/review_insights/alerts.py`: a short list of alert words applied after the model. Strong words (morboso/a, me besó, acoso, sin permiso, mamacita, nos caímos, se soltó, sin apretar, superintendencia, cobraron dos veces…) raise a review to `urgent`; weak words that also appear in positive reviews (garantía, reclamo, caída, incómodo, freno…) raise it to at least `review`. The net only raises severity, never lowers it, and the reason shown to the owner names the word that triggered it. Run `v2` = the v1 model output with the net applied, so the model is unchanged.

**Before measuring, a held-out set was committed** (`5f20081`): 16 new classifier cases, including alert words in positive contexts ("no me pasó nada en la caída", "me tocó esperar"), to measure false alarms.

## Results: classifier

| | v1 real | **v2 real** | v1 synthetic | **v2 synthetic** | v1 held-out | **v2 held-out** |
|---|---|---|---|---|---|---|
| S1 urgent recall | 3/4 | **4/4** | 14/17 | **15/17** | 6/8 | **8/8** |
| S2 actionable recall | 13/14 | **14/14** | 29/32 | 29/32 | 11/12 | **12/12** |
| S3 actionable precision | 13/13 | 14/14 | 29/30 | 29/30 | 11/12 | **12/15** |

On the 997 real comments the net fires on exactly 4, all genuinely actionable: zero false alarms on real data.

## What got worse

- **False alarms on held-out cases**: "Gracias al casco… no me pasó nada en la caída" and "La garantía me la respondieron en un día" are now `review` (precision 11/12 → 12/15). They are raised only to `review`, not `urgent`, by design.
- **Misspellings defeat word lists**: "no lo **quicieron** cambiar" (S0027) is not caught, because the pattern expects "quisieron".
- **Maintenance**: the list has to be kept by hand, and it only knows the words someone thought of.

## Caveat on the held-out result

The held-out cases were written by the same person (Claude) who wrote the alert list, right before it, so some overlap in vocabulary is likely ("morboso", "mamacita"). The real-data result (4/4, no false alarms) is the stronger evidence, and the strongest test would be reviews collected after this date.

## Q&A: attempts that did not move the score

Two further changes were tried and measured on both question sets; neither changed the score beyond run-to-run noise (12–13/25 between identical runs):

| Change | Dev questions (25) | Held-out questions (15) |
|---|---|---|
| Baseline: relevance filter, v1 labels (`../qa/qa_v2_relevance_filter.md`, `../qa/heldout_before.md`) | 15/25 | 10/15 |
| + filter rule "praise that mentions the topic is relevant" + v2 labels for retrieval | 15/25 | 10/15 |
| + classifier label shown next to each review (`qa_dev_after.md`, `qa_heldout_after.md`) | 14/25 | 10/15 (H06 0/2 → 1/2) |

Diagnosis on H06 ("¿Algún cliente se sintió acosado o incómodo con un empleado?"): after the safety net, retrieval returns both R01301 and R00309, but the local model's relevance check rejects them, and the answer cites an unrelated review instead. With the label shown, it keeps R01301 but still drops R00309. For meaning questions, the 7B local model is now the limit; the obvious next step is comparing a larger model or Claude on the same questions.
