"""Retrieval recall: are the reviews a correct answer must cite among the top-k results?

Usage: python scripts/eval_retrieval.py [-k 20] [--mode plain|labeled]
"""
import argparse
import json
import sys
from pathlib import Path

from review_insights.db import connect
from review_insights import retrieve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", type=int, default=20)
    parser.add_argument("--mode", default="plain", choices=["plain", "labeled"])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    conn = connect()
    questions = [q for q in json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))["questions"]
                 if q["type"] in ("meaning", "hybrid")]
    lines = [f"# Retrieval recall@{args.k} ({args.mode})", "", "| Question | Found | Missing |", "|---|---|---|"]
    found_total = needed_total = 0
    for q in questions:
        hits = retrieve.search(conn, q["question"], k=args.k) if args.mode == "plain" else \
            retrieve.search_labeled(conn, q["question"], k=args.k)
        ids = {h["review_id"] for h in hits}
        found = [r for r in q["must_cite"] if r in ids]
        missing = [r for r in q["must_cite"] if r not in ids]
        found_total, needed_total = found_total + len(found), needed_total + len(q["must_cite"])
        lines.append(f"| {q['id']} {q['question']} | {len(found)}/{len(q['must_cite'])} | {', '.join(missing) or '—'} |")
    lines += ["", f"**Total: {found_total}/{needed_total} required reviews retrieved**"]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
