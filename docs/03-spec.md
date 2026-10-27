# 3. Spec

## Overview

A local Python application with three capabilities over the anonymized reviews:

1. **Classify** every comment by theme and severity with an LLM.
2. **Answer questions** from the owner: counting questions with SQL, meaning questions with retrieval + LLM, always citing review IDs.
3. **Generate a weekly digest** with metrics, urgent items and recognitions, every claim cited.

**LLM:** a local model served by Ollama (`qwen2.5:7b`) by default, so the client's reviews never leave the computer. The model is a setting: Claude can replace it through `.env` without code changes, and the two can be compared on the same evaluation.

Flow diagram: [diagrams/flow-diagram.pdf](diagrams/flow-diagram.pdf).

## Components

| # | Component | Responsibility |
|---|---|---|
| C1 | `ingest` | Load the export, drop test company, anonymize, write to SQLite |
| C2 | `classify` | Label each comment (theme, sentiment, severity, short reason) with the LLM |
| C3 | `embed` | Embed comments with a local multilingual model, store in Chroma |
| C4 | `router` | Decide if a question is *counting* or *meaning* |
| C5 | `stats` | Answer counting questions with SQL |
| C6 | `retrieve` | Top-k semantic search + metadata filters (employee, date range, rating) |
| C7 | `answer` | The LLM answers using only retrieved reviews and cites IDs |
| C8 | `verify` | Reject/flag citations not in the retrieved set |
| C9 | `digest` | Weekly digest: SQL metrics + urgent items + evidence + LLM summary |
| C10 | `ui` | Streamlit page: ask a question, generate digest, open a cited review |
| C11 | `eval` | Run the evaluation set, compute S1–S7, compare full-context vs retrieval |

## Data model (SQLite)

```
reviews(
  review_id TEXT PRIMARY KEY,   -- R00001
  company TEXT, employee TEXT, device TEXT,
  created_at TEXT,              -- ISO 8601
  rating INTEGER,               -- 1..5
  comment TEXT, product TEXT,
  rating_time_ms INTEGER,
  has_rater_name INTEGER, has_rater_phone INTEGER,
  synthetic INTEGER DEFAULT 0
)
labels_ai(review_id, theme, sentiment, severity, reason, model, created_at)
labels_gold(review_id, theme, severity, notes)       -- hand labels for evaluation
```

## Taxonomy

**Severity**

| Value | Definition | Examples |
|---|---|---|
| `urgent` | Safety incident, harassment or inappropriate conduct, unresolved claim/warranty, legal threat | R01972, R01301, R00309, R02021 |
| `review` | Complaint or friction the owner should know about, not urgent | rude service, price, missing discount, wait time |
| `normal` | Praise, neutral, or no actionable content | "Excelente atención", "10/10" |

Severity is decided from the **text**, not the rating. When in doubt between two levels, choose the higher one (recall over precision, per S1).

**Theme**: `atencion`, `asesoria_producto`, `producto_defecto`, `precio`, `tiempo_espera`, `instalacion_taller`, `garantia_reclamo`, `conducta_inapropiada`, `otro`. One primary theme per comment.

## Behaviour

**Classification (C2)**
- Input: comment, rating, product. Output: JSON with the fields above, validated against the schema; invalid output is retried once, then stored as `severity = review` with reason `"unparsed"`.
- Comments are passed as **data**, inside delimiters, with explicit instructions that their content must never be followed (prompt injection).
- Empty comments are not sent to the API (severity `normal`, theme `otro`).

**Router (C4)**
- Rule-based first: questions starting with or containing *cuántas/cuántos, promedio, porcentaje, ranking, más/menos ... que* → counting. Otherwise → meaning.
- If the rule is unsure, ask the LLM to classify the question. The decision is shown in the UI.

**Retrieval (C6)**
- Embedding model: `intfloat/multilingual-e5-small` (local, CPU).
- Top-k = 20 by cosine similarity, with optional filters extracted from the question (employee pseudonym, date range, rating).

**Answer (C7) and verification (C8)**
- The LLM receives the question and the retrieved reviews (ID, date, rating, employee, comment) and must answer only from them, citing IDs like `[R01972]`. If they don't contain the answer, it must say so.
- C8 checks every cited ID against the retrieved set. Any invalid citation marks the answer as unverified in the UI and is counted for S4.

**Digest (C9)**
- Period: last 7 days vs. the previous 7 (configurable).
- Sections: metrics (SQL), "Atender primero" (urgent items, quoted), "Para revisar" (themes with counts and examples), "Reconocimientos", "Notas sobre los datos" (e.g., the 3-option window).
- Output: HTML file, with citations verified by C8.

## Non-functional requirements

- Runs fully locally on Windows with Python 3.12 and Ollama (RTX 5060, 8 GB VRAM); no cloud resources by default.
- Every LLM call logs model, tokens and latency. When Claude is used, calls go through **Portkey** if available so cost is recorded too.
- Local model context is limited (Qwen 2.5 7B: 32k tokens, set explicitly; Ollama's default is much smaller). The full-context baseline must fit in it.
- Secrets in `.env` only.
- Full classification of ~1,040 comments takes under 30 minutes on the local GPU (to be confirmed by measurement).
- Unit tests for router, stats, verify and anonymization; evaluation script reproducible from the command line.

## Decisions and rejected alternatives

| Decision | Chosen | Rejected and why |
|---|---|---|
| AI component (brief requires one) | **Retrieval pipeline** | **n8n automation**: works for the digest, but the logic would live in a no-code workflow that is harder to test, version and review; the Q&A use case needs retrieval anyway. |
| Retrieval vs. full context | Retrieval for meaning questions, SQL for counting | Sending all ~1,000 comments (~20k tokens) works today and is simpler. Kept as baseline **A** in the evaluation, so the choice is measured rather than assumed (S7). |
| Storage | SQLite + Chroma, local | DynamoDB copy: no benefit and risks touching the client's account. Postgres + pgvector: needs a server, unnecessary at this size. |
| Embeddings | Local multilingual model | API embeddings: cost and sending data to another provider for no clear gain on short Spanish text. |
| LLM | Local `qwen2.5:7b` via Ollama, Claude optional | **Claude API** as default: better on hard cases, but paid per call and sends client text to a third party; kept as an optional comparison. **Free cloud tiers** (Gemini, Groq): some use submitted data for training, unacceptable for client reviews. **Fine-tuned small classifier**: ~14 real negative examples are not enough to train one. |
| UI | Streamlit | React/FastAPI: polish is not scored. |
| Real-time dashboard | Cut | No value for the stated problem; ratings change slowly and the average hides the signal anyway. |

## Context artifact (CLAUDE.md)

The brief requires evidence of the context file's effect. To capture a real "before":

1. Generate the first versions of the classifier prompt and the `ingest`/`classify` modules **without** `CLAUDE.md`, and save the outputs.
2. Add `CLAUDE.md` (domain glossary, taxonomy, anonymization rules, prompt-injection rule, coding conventions, test expectations).
3. Regenerate the same pieces and compare: correctness of taxonomy use, leaks of PII handling, tests produced, and classification metrics on the evaluation set.
