"""Semantic search over review comments.

Embeddings come from a local Ollama model (bge-m3, multilingual) and are stored in SQLite.
At ~1,000 short comments a brute-force cosine scan is fast enough, so no vector database.

Usage:
    python -m review_insights.retrieve index
    python -m review_insights.retrieve search "¿Algún cliente tuvo un accidente?"
"""
import argparse
import json
import math
import os
import sys
import urllib.request
from array import array

from review_insights.db import connect
from review_insights.llm import load_env

EMBED_MODEL = "bge-m3"

SCHEMA = """CREATE TABLE IF NOT EXISTS embeddings (
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    model TEXT NOT NULL,
    vector BLOB NOT NULL,
    PRIMARY KEY (review_id, model)
)"""


def embed(texts):
    load_env()
    url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/embed"
    body = json.dumps({"model": EMBED_MODEL, "input": texts}).encode()
    request = urllib.request.Request(url, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        vectors = json.load(response)["embeddings"]
    return [_normalize(v) for v in vectors]


def _normalize(vector):
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def document_text(review):
    """What gets embedded: the comment, plus the product when there is one."""
    text = " ".join(review["comment"].split())
    return f"{text} (Producto: {review['product'].strip()})" if (review["product"] or "").strip() else text


def index(conn, batch_size=64):
    """Embeds real reviews with a comment that are not indexed yet. Synthetic cases are left out:
    they exist to test the classifier, and would distort answers about the store."""
    conn.execute(SCHEMA)
    pending = conn.execute(
        """SELECT * FROM reviews WHERE synthetic = 0 AND trim(coalesce(comment, '')) != ''
           AND review_id NOT IN (SELECT review_id FROM embeddings WHERE model = ?)""", (EMBED_MODEL,)).fetchall()
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        vectors = embed([document_text(r) for r in batch])
        with conn:
            conn.executemany("INSERT INTO embeddings VALUES (?, ?, ?)",
                             [(r["review_id"], EMBED_MODEL, array("f", v).tobytes()) for r, v in zip(batch, vectors)])
    return len(pending)


def search(conn, query, k=20, employee=None, date_from=None, date_to=None, max_rating=None):
    """Top-k reviews by cosine similarity, after optional metadata filters."""
    conn.execute(SCHEMA)
    where, params = ["e.model = ?"], [EMBED_MODEL]
    for clause, value in [("r.employee = ?", employee), ("r.created_at >= ?", date_from),
                          ("r.created_at < ?", date_to), ("r.rating <= ?", max_rating)]:
        if value is not None:
            where.append(clause)
            params.append(value)
    rows = conn.execute(f"""SELECT r.*, e.vector FROM embeddings e JOIN reviews r USING (review_id)
                            WHERE {' AND '.join(where)}""", params).fetchall()
    q = embed([query])[0]
    scored = []
    for row in rows:
        vector = array("f")
        vector.frombytes(row["vector"])
        scored.append((sum(a * b for a, b in zip(q, vector)), row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [{**{key: row[key] for key in row.keys() if key != "vector"}, "score": round(score, 4)}
            for score, row in scored[:k]]


def search_labeled(conn, query, k=20, run_id="v2", **filters):
    """Half the slots go to reviews the classifier flagged as actionable, half to plain search.

    Complaints are rare and often worded generically ("mala atención"), so plain similarity
    buries them under hundreds of compliments. Recall for complaints then depends on the classifier.
    """
    flagged = {row["review_id"] for row in conn.execute(
        "SELECT review_id FROM labels_ai WHERE run_id = ? AND severity IN ('urgent', 'review')", (run_id,))}
    ranked = search(conn, query, k=None, **filters)  # all of them: flagged reviews can rank low overall
    from_flagged = [h for h in ranked if h["review_id"] in flagged][:k // 2]
    chosen = {h["review_id"] for h in from_flagged}
    rest = [h for h in ranked if h["review_id"] not in chosen][:k - len(from_flagged)]
    return sorted(from_flagged + rest, key=lambda h: h["score"], reverse=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=10)
    args = parser.parse_args()

    conn = connect()
    if args.command == "index":
        print(f"indexed {index(conn)} reviews")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        for hit in search(conn, args.query, k=args.k):
            print(f"{hit['score']:.3f} {hit['review_id']} {hit['rating']}★ {' '.join(hit['comment'].split())[:100]}")


if __name__ == "__main__":
    main()
