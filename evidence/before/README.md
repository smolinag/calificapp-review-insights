# Before the context artifact

State of the classifier before `CLAUDE.md` existed.

## How the baseline was produced

- **Prompt `v0`** (`src/review_insights/classify.py`, `PROMPT_V0`) contains only the bare task: the review, and the allowed values for theme, sentiment and severity. No definitions of the values, no description of the store, no rule about treating the review as data, no examples.
- **Honest caveat.** The code was written by Claude Code in a session that already knew the domain from earlier discussion, so this is not a context-free generation in the strict sense. The baseline was made fair by restricting what reaches the *model at runtime* to what a developer would write from the task description alone. What `CLAUDE.md` changes is measured in the prompt and code generated after it, and in the metrics below.
- **Model:** `qwen2.5:7b` via Ollama, temperature 0, JSON mode. Same model for before and after, so differences come from context, not from the model.

## Files

- `classifier_v0.md`: metrics (S1–S3) for real and synthetic reviews, latency, and every error on an actionable decision with the model's stated reason.
