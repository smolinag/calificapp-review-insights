"""End-to-end Q&A evaluation on eval/questions.json (criteria S4-S6).

Usage: python scripts/eval_qa.py [--out evidence/qa/run.md]
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

from review_insights.answer import ask
from review_insights.db import connect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    conn = connect()
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))["questions"]
    rows, correct, invalid_total, latencies = [], 0, 0, []
    for q in questions:
        r = ask(conn, q["question"])
        latencies.append(r["latency_ms"])
        invalid_total += len(r["invalid_citations"])
        must = set(q.get("must_cite", []))
        cited = set(r["citations"])
        if q["type"] == "counting":
            ok = str(r["answer"]).split(" ")[0].rstrip(".") in str(q["answer"])
            verdict = "OK" if ok else f"expected {q['answer']}"
        elif q["type"] == "hybrid":
            ok = str(r["answer"]).startswith(str(q["answer"])) and must <= cited
            verdict = "OK" if ok else f"expected {q['answer']} citing {sorted(must)}"
        elif not must:  # correct answer is "there are none"
            ok = not cited
            verdict = "OK" if ok else "cited reviews when none apply"
        else:
            found = must & cited
            ok = found == must
            verdict = "OK" if ok else f"cited {len(found)}/{len(must)}; missing {', '.join(sorted(must - found))}"
        correct += ok
        answer = " ".join(r["answer"].split()).replace("|", "/")
        rows.append(f"| {q['id']} | {q['question']} | {r['route']} | {answer[:220]} | {verdict} |")
        print(q["id"], r["route"], verdict, flush=True)

    lines = ["# Q&A evaluation", "",
             f"**Correct: {correct}/{len(questions)}** · invalid citations (S4): {invalid_total} · "
             f"median latency {statistics.median(latencies)} ms", "",
             "Meaning questions count as correct only if every required review is cited. "
             "Answers are not otherwise judged for wording.", "",
             "| Q | Question | Route | Answer | Verdict |", "|---|---|---|---|---|", *rows]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
