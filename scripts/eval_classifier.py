"""Scores a classification run against the gold labels (success criteria S1-S3).

Usage: python scripts/eval_classifier.py v0 [--out evidence/before/classifier_v0.md]
"""
import argparse
import statistics
import sys
from pathlib import Path

from review_insights.db import connect

ACTIONABLE = {"urgent", "review"}


def score(rows):
    urgent = [r for r in rows if r["gold"] == "urgent"]
    actionable = [r for r in rows if r["gold"] in ACTIONABLE]
    flagged = [r for r in rows if r["pred"] in ACTIONABLE]
    hit = lambda rs, ok: sum(r["pred"] in ok for r in rs)
    true_flags = sum(r["gold"] in ACTIONABLE for r in flagged)
    themed = [r for r in actionable if r["pred"] in ACTIONABLE]
    return {
        "n": len(rows),
        "S1 urgent recall": f"{hit(urgent, {'urgent'})}/{len(urgent)}",
        "urgent flagged at least as review": f"{hit(urgent, ACTIONABLE)}/{len(urgent)}",
        "S2 actionable recall": f"{hit(actionable, ACTIONABLE)}/{len(actionable)}",
        "S3 actionable precision": f"{true_flags}/{len(flagged)}",
        "theme correct (actionable, flagged)": f"{sum(r['theme'] == r['gold_theme'] for r in themed)}/{len(themed)}",
        "exact severity": f"{sum(r['pred'] == r['gold'] for r in rows)}/{len(rows)}",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows = [dict(r) for r in connect().execute(
        """SELECT l.review_id, r.synthetic, r.rating, r.comment, l.severity AS pred, l.theme, l.reason,
                  l.latency_ms, l.model, g.severity AS gold, g.theme AS gold_theme, g.note
           FROM labels_ai l JOIN reviews r USING (review_id) JOIN labels_gold g USING (review_id)
           WHERE l.run_id = ? ORDER BY l.review_id""", (args.run_id,))]
    if not rows:
        raise SystemExit(f"no labels for run {args.run_id}")

    lines = [f"# Classifier run `{args.run_id}`", "", f"Model: `{rows[0]['model']}` · reviews scored: {len(rows)}", "",
             "| Metric | Real | Synthetic | Held-out |", "|---|---|---|---|"]
    sets = [score([r for r in rows if r["synthetic"] == flag]) for flag in (0, 1, 2)]
    for key in sets[0]:
        lines.append(f"| {key} | " + " | ".join(str(s[key]) for s in sets) + " |")
    latencies = [r["latency_ms"] for r in rows]
    lines += ["", f"Latency per review: median {statistics.median(latencies)} ms, "
                  f"p90 {sorted(latencies)[int(len(latencies) * .9)]} ms, total {sum(latencies) / 60000:.1f} min", ""]

    misses = [r for r in rows if (r["gold"] in ACTIONABLE) != (r["pred"] in ACTIONABLE) or
              (r["gold"] == "urgent" and r["pred"] != "urgent")]
    lines += ["## Errors on actionable decisions", "",
              "| Review | Rating | Comment | Gold | Predicted | Model's reason |", "|---|---|---|---|---|---|"]
    for r in sorted(misses, key=lambda r: (r["synthetic"], r["gold"] != "urgent", r["review_id"])):
        comment = " ".join(r["comment"].split())[:90].replace("|", "/")
        reason = " ".join((r["reason"] or "").split())[:90].replace("|", "/")
        lines.append(f"| {r['review_id']} | {r['rating']} | {comment} | {r['gold']} | {r['pred']} | {reason} |")

    report = "\n".join(lines) + "\n"
    sys.stdout.reconfigure(encoding="utf-8")  # comments contain emoji; the Windows console default can't print them
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
