"""Labels each review comment with theme, sentiment and severity using the LLM.

Usage: python -m review_insights.classify --run-id v0 [--prompt v0] [--limit N] [--synthetic-only]
Resumable: reviews already labeled for the run are skipped.
"""
import argparse
import json

from review_insights import llm
from review_insights.db import connect

THEMES = ["atencion", "asesoria_producto", "producto_defecto", "precio", "tiempo_espera",
          "instalacion_taller", "garantia_reclamo", "conducta_inapropiada", "otro"]
SEVERITIES = ["urgent", "review", "normal"]
SENTIMENTS = ["positive", "neutral", "negative"]

# v0: the bare task, without domain context (baseline for the context-artifact comparison)
PROMPT_V0 = """Classify this customer review.

Rating: {rating}/5
Product: {product}
Review: {comment}

Return JSON with keys: theme (one of: {themes}), sentiment (one of: {sentiments}), severity (one of: {severities}), reason (short)."""

PROMPTS = {"v0": (None, PROMPT_V0)}


def _parse(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if data.get("severity") not in SEVERITIES:
        return None
    return {
        "theme": data.get("theme") if data.get("theme") in THEMES else "otro",
        "sentiment": data.get("sentiment") if data.get("sentiment") in SENTIMENTS else None,
        "severity": data["severity"],
        "reason": str(data.get("reason", ""))[:300],
    }


def classify(review, prompt_name="v0"):
    system, template = PROMPTS[prompt_name]
    prompt = template.format(rating=review["rating"], product=review["product"] or "-", comment=review["comment"],
                             themes=", ".join(THEMES), sentiments=", ".join(SENTIMENTS),
                             severities=", ".join(SEVERITIES))
    total_in = total_out = latency = 0
    for _ in range(2):  # one retry on invalid output
        completion = llm.complete(prompt, system=system, json_mode=True, max_tokens=200)
        total_in += completion.input_tokens or 0
        total_out += completion.output_tokens or 0
        latency += completion.latency_ms
        label = _parse(completion.text)
        if label:
            break
    else:
        label = {"theme": "otro", "sentiment": None, "severity": "review", "reason": "unparsed"}
    return {**label, "model": completion.model, "input_tokens": total_in, "output_tokens": total_out,
            "latency_ms": latency}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--prompt", default="v0", choices=PROMPTS)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--synthetic-only", action="store_true")
    args = parser.parse_args()

    conn = connect()
    query = """SELECT r.* FROM reviews r
               WHERE trim(coalesce(r.comment, '')) != ''
                 AND r.review_id NOT IN (SELECT review_id FROM labels_ai WHERE run_id = ?)"""
    if args.synthetic_only:
        query += " AND r.synthetic = 1"
    query += " ORDER BY r.synthetic DESC, r.review_id"
    pending = conn.execute(query, (args.run_id,)).fetchall()[:args.limit]
    print(f"{len(pending)} reviews to classify (run {args.run_id}, prompt {args.prompt})", flush=True)

    for n, review in enumerate(pending, 1):
        label = classify(review, args.prompt)
        with conn:
            conn.execute(
                """INSERT INTO labels_ai (review_id, run_id, theme, sentiment, severity, reason, model,
                                          input_tokens, output_tokens, latency_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (review["review_id"], args.run_id, label["theme"], label["sentiment"], label["severity"],
                 label["reason"], label["model"], label["input_tokens"], label["output_tokens"], label["latency_ms"]))
        if n % 50 == 0 or n == len(pending):
            print(f"{n}/{len(pending)}", flush=True)


if __name__ == "__main__":
    main()
