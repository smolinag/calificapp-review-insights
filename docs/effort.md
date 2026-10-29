# Declared effort

**Approximate total: 6 hours**, of which:

| Activity | Hours |
|---|---|
| Discovery: understanding the Calificapp backend and data export, owner permission | 1 |
| Data: anonymization, manual PII review, synthetic and held-out cases, gold labels, evaluation questions | 1 |
| Build: classifier, retrieval, router, answers, web page | 2 |
| Evaluation, failure analysis, AI review, pitch and demo | 2 |

Commits run from 2026-10-27 (spec, plan and tasks first) to 2026-10-29. Code, prompts and synthetic data were generated with Claude Code; labels, data decisions and review were the author's.

## What was cut, and why

| Cut | Why | Effect |
|---|---|---|
| **Weekly digest (T17)**, promised in the problem statement as the first thing that changes for the owner | Time went to the part with the highest cost of failure: finding urgent reviews (S1) and measuring Q&A honestly. The web page's flagged list covers "atender primero" | No weekly comparison or recognitions section; the owner has to open the page |
| **Claude as the model on the same evaluation** | Local model chosen so client reviews never leave the computer; the comparison needs an API key and the owner's consent to send text out | Unknown how much of the Q&A gap (15/25) a larger model would close, though the evidence points to the model (`evidence/improvement/README.md`) |
| **A check that each citation supports its claim** | The ID check (S4) was built; checking support needs another model call per citation | Wrong-but-valid citations pass (`docs/failure-analysis.md` F10, F13) |
| **Relative dates and months without a year in counting questions** | Found in the final failure hunt | "¿Cuántas reseñas hubo en septiembre?" answers 3184 instead of 274 (F17) |
| **Portkey cost tracking** | No paid API calls: the model is local, so cost per question is GPU time; tokens and latency are logged instead | — |
| Real-time dashboard, authentication, multi-store, deployment | Out of scope from the start (problem statement) | — |
