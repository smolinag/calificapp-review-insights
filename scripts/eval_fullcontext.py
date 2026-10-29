"""S7: full context (A) vs retrieval (B) on the meaning questions of both question sets.

A sends every real comment in one prompt; B is the normal pipeline (`answer.ask`). Both run in the same session,
so latencies are comparable. Tokens are summed over every model call a question makes.

Usage: python scripts/eval_fullcontext.py [--out evidence/eval_fullcontext.md]
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from review_insights import answer, llm
from review_insights.db import connect

QUESTION_FILES = [Path("eval/questions.json"), Path("eval/questions_heldout.json")]
NUM_CTX = 32768

_real_complete = llm.complete
calls = []


def counting_complete(*args, **kwargs):
    completion = _real_complete(*args, **kwargs)
    calls.append(completion)
    return completion


llm.complete = counting_complete  # answer.ask looks llm.complete up at call time


def all_comments(conn):
    rows = conn.execute("SELECT review_id, created_at, rating, employee, comment, product FROM reviews "
                        "WHERE synthetic = 0 AND trim(coalesce(comment, '')) != '' ORDER BY review_id").fetchall()
    return [dict(r) for r in rows]


def full_context(question, reviews):
    text = "\n".join(f"[{r['review_id']}] {r['rating']}★: {' '.join(r['comment'].split())}" for r in reviews)
    completion = llm.complete(f"Pregunta: {question}\n\n<reseñas>\n{text}\n</reseñas>", system=answer.SYSTEM,
                              max_tokens=500, num_ctx=NUM_CTX)
    cited, invalid = answer.verify(completion.text, {r["review_id"] for r in reviews})
    return completion.text, cited, invalid


def grade(q, cited):
    must = set(q.get("must_cite", []))
    if not must:
        return not cited, "OK" if not cited else "cited reviews when none apply"
    found = must & set(cited)
    return found == must, "OK" if found == must else f"cited {len(found)}/{len(must)}"


def run_timed(fn):
    calls.clear()
    start = time.perf_counter()
    result = fn()
    latency = int((time.perf_counter() - start) * 1000)
    tokens_in = sum(c.input_tokens or 0 for c in calls)
    return result, latency, tokens_in, len(calls)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    conn = connect()
    reviews = all_comments(conn)

    rows, totals = [], {"A": [], "B": []}
    for path in QUESTION_FILES:
        for q in json.loads(path.read_text(encoding="utf-8"))["questions"]:
            if q["type"] != "meaning":
                continue
            (text_a, cited_a, invalid_a), lat_a, tok_a, n_a = run_timed(lambda: full_context(q["question"], reviews))
            r, lat_b, tok_b, n_b = run_timed(lambda: answer.ask(conn, q["question"]))
            ok_a, verdict_a = grade(q, cited_a)
            ok_b, verdict_b = grade(q, r["citations"])
            totals["A"].append((path.stem, ok_a, lat_a, tok_a, len(invalid_a)))
            totals["B"].append((path.stem, ok_b, lat_b, tok_b, len(r["invalid_citations"])))
            rows.append(f"| {q['id']} | {q['question']} | {verdict_a} | {verdict_b} | {lat_a} / {lat_b} | "
                        f"{tok_a} / {tok_b} ({n_b} calls) |")
            print(q["id"], verdict_a, "|", verdict_b, flush=True)

    def summary(name, label):
        t = totals[name]
        by_set = " · ".join(f"{s}: {sum(ok for st, ok, *_ in t if st == s)}/{sum(st == s for st, *_ in t)}"
                            for s in [p.stem for p in QUESTION_FILES])
        return (f"| {label} | {by_set} | {statistics.median(x[2] for x in t)} ms | "
                f"{statistics.median(x[3] for x in t)} | {sum(x[4] for x in t)} |")

    lines = ["# S7: full context (A) vs retrieval (B), meaning questions", "",
             f"Model: `{llm.settings()[1]}` · A: all {len(reviews)} real comments in one prompt (num_ctx {NUM_CTX}) · "
             "B: `answer.ask` (router, retrieval k=20, relevance filter, answer). Same session, same GPU.", "",
             "| Mode | Correct | Median latency | Median input tokens per question | Invalid citations |",
             "|---|---|---|---|---|", summary("A", "A full context"), summary("B", "B retrieval"), "",
             "| Q | Question | A | B | Latency ms A / B | Input tokens A / B |", "|---|---|---|---|---|---|", *rows]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
