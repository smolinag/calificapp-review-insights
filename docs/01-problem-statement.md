# 1. Problem statement

## Domain

Retail customer service. The client is a motorcycle-gear store (helmets, tyres, rain gear, accessories) that uses **Calificapp**: tablets at the counter where customers rate the employee who served them (1–5) and optionally leave a comment, the product they bought, their name and phone.

## User

The **store owner / manager**. Not technical, no time to read comments, looks at the numbers occasionally.

## Problem

The store collects ~250 ratings a month (3,184 between Oct 2025 and Oct 2026). The ratings say everything is fine:

- 93% are 5 stars, 6% are 4, only ~1% are 3 or lower.
- The monthly average never moves from ~4.9.

But about a third of the ratings carry a comment, and buried among ~1,000 near-identical "Excelente atención" there are reviews the owner must act on and has never seen (IDs refer to the anonymized dataset):

| Review | Rating | Content (paraphrased) | Why it matters |
|---|---|---|---|
| R01972 | 1 | A tyre fitted by the store failed and the customer crashed | Safety incident, possible liability |
| R01301 | 1 | Customer reports an employee kissed them instead of shaking hands | Possible harassment |
| R00309 | **5** | "Excellent service, but very lewd" | Inappropriate conduct hidden in a 5-star rating |
| R02021 | 1 | Warranty claim on a helmet, no solution given | Unresolved claim |
| R00460, R00933 | 5 | "...but the discount was missing", "...although prices are high" | Price friction inside top ratings |
| R01351 | 5 | Customer asks for an excellence recognition for an employee | Positive action the owner can take |

Nobody reads the comments, so these go unnoticed. The ratings also expire: the backend deletes them after 500 days, so the history is lost if it is not analysed.

## What changes for the user if this works

1. Each week the owner receives a short **digest**: what needs attention first (with the exact reviews quoted), how this week compares to the last, and who deserves recognition.
2. The owner can **ask questions** in plain Spanish ("¿Algún cliente tuvo un accidente?", "¿Qué dicen de los cascos?") and get answers that cite the reviews they come from.
3. Counting questions ("¿Cuántas reseñas de 1 estrella hubo en septiembre?") are answered with exact numbers computed from the data, not by the model.

## Definition of success

Measured on a hand-labeled evaluation set (all real reviews with a comment, plus hand-written synthetic hard cases, **reported separately**):

| # | Criterion | Target |
|---|---|---|
| S1 | Recall of **urgent** reviews (safety, harassment / inappropriate conduct, unresolved claims) | **100%** — missing one costs far more than a false alarm |
| S2 | Recall of **actionable** reviews (urgent + "review") | ≥ 90% |
| S3 | Precision of actionable flags | ≥ 60% (the owner tolerates some noise, not a flood) |
| S4 | Grounding: citations in answers and digests that point to a non-existent review or to one not retrieved for that answer | **0** |
| S5 | Q&A: questions in the evaluation set answered correctly against the answer key | ≥ 80% |
| S6 | Counting questions answered with the exact number | 100% (they go to SQL, not the model) |
| S7 | Retrieval vs. sending all comments in the prompt: cost and latency per question | Measured and reported, including where retrieval is worse |

## Out of scope

- Real-time dashboard, authentication, multi-store support, deployment.
- Writing anything back to the client's DynamoDB or changing the Calificapp app/backend.
- Fixing the backend security issues found during discovery (listed in the AI review as observations only).
