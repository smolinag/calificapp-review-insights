# Calificapp Review Insights

Prototype for the Perficient Global AI-First Academy capstone (L1 · Case 05 · Open Choice).

A store using [Calificapp](../Calificapp) tablets collects ~250 customer ratings a month. The average is ~4.9/5, so the owner concludes everything is fine — but a handful of reviews that need action (a crash after a tyre fitting, possible harassment, unresolved warranty claims) sit unread among ~1,000 near-identical compliments. This prototype surfaces them with evidence, produces a weekly digest, and lets the owner ask questions about their reviews.

## Documents (written before any code)

| # | Document | What it covers |
|---|---|---|
| 1 | [Problem statement](docs/01-problem-statement.md) | Domain, user, problem, definition of success |
| 2 | [Data provenance](docs/02-data-provenance.md) | Source, what the data does and does not represent, sensitive-data handling |
| 3 | [Spec](docs/03-spec.md) | What the system does, architecture, decisions and rejected alternatives |
| 4 | [Plan](docs/04-plan.md) | Build order and how each phase maps to the submission checklist |
| 5 | [Tasks](docs/05-tasks.md) | Task breakdown with acceptance criteria |
| — | [Flow diagram](docs/diagrams/flow-diagram.pdf) | As planned, in Spanish, before the code: data preparation, Q&A, weekly digest and evaluation flows |
| — | [Flow diagram, as built](docs/diagrams/flow-diagram-en.pdf) | English. What was actually built: SQLite vectors, alert words, three routes, relevance check; the weekly digest marked as cut |

## Run it

Requires Python 3.12 and [Ollama](https://ollama.com) with `qwen2.5:7b` and `bge-m3` pulled. Everything runs on this computer.

```
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev,app]"
.venv/Scripts/python -m review_insights.db                          # build data/reviews.db
.venv/Scripts/python -m review_insights.classify --run-id v1        # label comments (~15 min on GPU)
.venv/Scripts/python -m review_insights.classify --run-id v2 --derive-from v1   # + alert words
.venv/Scripts/python -m review_insights.retrieve index              # embeddings (~1 min)
.venv/Scripts/streamlit run src/review_insights/app.py             # http://localhost:8501
```

## Submission

| Brief item | Where |
|---|---|
| Problem statement, data provenance | `docs/01-problem-statement.md`, `docs/02-data-provenance.md` |
| Spec, plan, tasks (committed before the code: `ace1f23`) | `docs/03-spec.md`, `docs/04-plan.md`, `docs/05-tasks.md` |
| Context artifact and before/after evidence | `CLAUDE.md`, `evidence/before/`, `evidence/after/README.md` |
| Flow diagram (as built, English) | `docs/diagrams/flow-diagram-en.pdf` |
| Retrieval pipeline and why not n8n | `src/review_insights/retrieve.py`, spec § Decisions |
| Results against the definition of success (S1–S7) | `evidence/eval_results.md` |
| Measured improvement (before, change, after, what got worse) | `evidence/improvement/README.md` |
| AI output review | `docs/ai-review.md` (running log: `docs/ai-review-log.md`) |
| Failure analysis | `docs/failure-analysis.md` |
| Pitch slide | `docs/pitch.pdf` |
| Demo transcript | `docs/demo.md` |
| Declared effort and what was cut | `docs/effort.md` |

## Status

Working prototype: classification of every comment, Q&A with citations, web page. On the 997 real comments it flags all 14 actionable reviews (4/4 urgent) with no false alarms; open-ended questions are answered correctly about half the time (`evidence/eval_results.md`). The weekly digest promised in the problem statement was cut (`docs/effort.md`).
