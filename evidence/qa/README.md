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
