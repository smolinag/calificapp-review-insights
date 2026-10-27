"""Builds data/labels_gold.csv: the reference labels used to evaluate the classifier.

Every real comment was read (long ones one by one, short ones after filtering out plain praise).
Plain praise is `normal`; everything else is listed below with the reason for its label.
Synthetic cases carry their labels in data/synthetic_cases.csv.

Usage: python scripts/build_gold_labels.py
"""
import csv
import json
import re
from pathlib import Path

# review_id -> (severity, theme, note)
EXCEPTIONS = {
    # urgent: safety, inappropriate conduct by staff, unresolved claims
    "R01972": ("urgent", "instalacion_taller", "Tyre fitted by the store failed; customers crashed"),
    "R01301": ("urgent", "conducta_inapropiada", "Employee kissed the customer"),
    "R00309": ("urgent", "conducta_inapropiada", "Lewd behaviour reported inside a 5-star rating"),
    "R02021": ("urgent", "garantia_reclamo", "Helmet claim filed, no solution"),
    # review: complaints and friction
    "R00355": ("review", "atencion", "Bad service, no detail"),
    "R03045": ("review", "atencion", "Bad service, no detail"),
    "R01576": ("review", "atencion", "Did not like service from staff upstairs"),
    "R02123": ("review", "atencion", "Refused to show a size; another branch did. Ends in thanks"),
    "R02838": ("review", "atencion", "Bad service from the salesperson"),
    "R03023": ("review", "asesoria_producto", "Inexperienced; someone else had to do the job"),
    "R02412": ("review", "otro", "Ambiguous: reads as written by staff ('no le gustó la hora')"),
    "R00460": ("review", "precio", "Discount was missing"),
    "R00933": ("review", "precio", "Prices are high"),
    "R01215": ("review", "otro", "Customer asks to be called when an ordered item arrives"),
    # normal, but worth a note
    "R02888": ("normal", "atencion", "Ambiguous: customer compliments the employee's eyes; no staff misconduct"),
    "R01801": ("normal", "atencion", "Mentions a complication that was solved"),
    "R01993": ("normal", "atencion", "'nos demoramos' refers to the customer taking long, not the store"),
    "R02740": ("normal", "atencion", "Customer dropped their helmet; employee fixed it"),
    "R01890": ("normal", "atencion", "Joke about owing a tip"),
}
# emoji/punctuation only, single letters, keyboard noise and placeholders; theme is only scored on
# review/urgent, so this only keeps the reference labels honest
NO_CONTENT = re.compile(r"^(?:[\W_]*|[a-z]|n/?a|ninguno|no|varios|aceite|esto es una prueba|bghh)$", re.I)
REPEATED_LETTERS = re.compile(r"^(\w)\1+$", re.I)


def main():
    rows = json.loads(Path("data/reviews_anon.json").read_text(encoding="utf-8"))
    labels = []
    for r in rows:
        text = " ".join((r["comment"] or "").split())
        if not text:
            continue
        if r["review_id"] in EXCEPTIONS:
            severity, theme, note = EXCEPTIONS[r["review_id"]]
        elif NO_CONTENT.match(text) or REPEATED_LETTERS.match(text):
            severity, theme, note = "normal", "otro", "No actionable content"
        else:
            severity, theme, note = "normal", "atencion", ""
        labels.append({"review_id": r["review_id"], "synthetic": 0, "severity": severity, "theme": theme, "note": note})

    with open("data/synthetic_cases.csv", encoding="utf-8") as f:
        for s in csv.DictReader(f):
            labels.append({"review_id": s["review_id"], "synthetic": 1, "severity": s["gold_severity"],
                           "theme": s["gold_theme"], "note": s["notes"]})

    with open("data/labels_gold.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["review_id", "synthetic", "severity", "theme", "note"])
        writer.writeheader()
        writer.writerows(labels)

    missing = set(EXCEPTIONS) - {l["review_id"] for l in labels}
    assert not missing, f"exceptions without a comment: {missing}"
    for synthetic in (0, 1):
        subset = [l for l in labels if l["synthetic"] == synthetic]
        counts = {s: sum(l["severity"] == s for l in subset) for s in ("urgent", "review", "normal")}
        print("synthetic" if synthetic else "real", len(subset), counts)


if __name__ == "__main__":
    main()
