"""Local SQLite store for reviews and labels.

Usage: python -m review_insights.db   (rebuilds data/reviews.db from the committed data files)
"""
import csv
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data/reviews.db")
REVIEWS_JSON = Path("data/reviews_anon.json")
SYNTHETIC_CSV = Path("data/synthetic_cases.csv")
HELDOUT_CSV = Path("data/heldout_cases.csv")  # synthetic = 2: never used to tune prompts or rules
GOLD_CSV = Path("data/labels_gold.csv")

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id TEXT PRIMARY KEY,
    company TEXT, employee TEXT, device TEXT,
    created_at TEXT,
    rating INTEGER,
    comment TEXT, product TEXT,
    rating_time_ms INTEGER,
    has_rater_name INTEGER, has_rater_phone INTEGER,
    synthetic INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS labels_ai (
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    run_id TEXT NOT NULL,
    theme TEXT, sentiment TEXT, severity TEXT, reason TEXT,
    model TEXT, input_tokens INTEGER, output_tokens INTEGER, latency_ms INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, run_id)
);
CREATE TABLE IF NOT EXISTS labels_gold (
    review_id TEXT PRIMARY KEY REFERENCES reviews(review_id),
    severity TEXT, theme TEXT, note TEXT
);
"""

COLUMNS = ["review_id", "company", "employee", "device", "created_at", "rating", "comment", "product",
           "rating_time_ms", "has_rater_name", "has_rater_phone", "synthetic"]


def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _synthetic_rows(path, flag=1):
    with open(path, encoding="utf-8") as f:
        for s in csv.DictReader(f):
            yield {"review_id": s["review_id"], "company": "COMPANY_02", "employee": s["employee"],
                   "device": None, "created_at": s["created_at"], "rating": int(s["rating"]),
                   "comment": s["comment"], "product": s["product"] or None, "rating_time_ms": None,
                   "has_rater_name": 0, "has_rater_phone": 0, "synthetic": flag}


def rebuild(conn, reviews_json=REVIEWS_JSON, synthetic_csv=SYNTHETIC_CSV, gold_csv=GOLD_CSV, heldout_csv=HELDOUT_CSV):
    """Replaces reviews and gold labels with the contents of the data files. AI labels are kept."""
    real = json.loads(Path(reviews_json).read_text(encoding="utf-8"))
    rows = [*real, *_synthetic_rows(synthetic_csv), *_synthetic_rows(heldout_csv, flag=2)]
    with conn:
        conn.execute("DELETE FROM labels_gold")
        conn.execute("DELETE FROM reviews")
        conn.executemany(
            f"INSERT INTO reviews ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
            [[int(r[c]) if isinstance(r[c], bool) else r[c] for c in COLUMNS] for r in rows],
        )
        with open(gold_csv, encoding="utf-8") as f:
            conn.executemany("INSERT INTO labels_gold VALUES (:review_id, :severity, :theme, :note)",
                             csv.DictReader(f))
    return len(real), len(rows) - len(real)


if __name__ == "__main__":
    conn = connect()
    real, synthetic = rebuild(conn)
    gold = conn.execute("SELECT COUNT(*) FROM labels_gold").fetchone()[0]
    print(f"{DB_PATH}: {real} real + {synthetic} synthetic reviews, {gold} gold labels")
