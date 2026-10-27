"""Answers counting questions with fixed, parameterized SQL. The model never writes SQL.

Filters: employee (EMP_xx), month (YYYY-MM), year (YYYY), rating, min_rating, max_rating,
product_contains, theme, actionable (bool: classifier severity urgent/review).
"""
from review_insights.classify import THEMES

LABEL_RUN = "v2"  # v1 model labels + alert words


def _where(filters):
    clauses, params = ["r.synthetic = 0"], []
    f = filters or {}
    if f.get("employee"):
        clauses.append("r.employee = ?"); params.append(f["employee"].upper())
    if f.get("month"):
        clauses.append("substr(r.created_at, 1, 7) = ?"); params.append(f["month"])
    if f.get("year"):
        clauses.append("substr(r.created_at, 1, 4) = ?"); params.append(str(f["year"]))
    if f.get("rating") is not None:
        clauses.append("r.rating = ?"); params.append(int(f["rating"]))
    if f.get("min_rating") is not None:
        clauses.append("r.rating >= ?"); params.append(int(f["min_rating"]))
    if f.get("max_rating") is not None:
        clauses.append("r.rating <= ?"); params.append(int(f["max_rating"]))
    if f.get("product_contains"):
        clauses.append("lower(coalesce(r.product, '')) LIKE ?"); params.append(f"%{f['product_contains'].lower()}%")
    needs_labels = f.get("theme") in THEMES or f.get("actionable")
    if f.get("theme") in THEMES:
        clauses.append("l.theme = ?"); params.append(f["theme"])
    if f.get("actionable"):
        clauses.append("l.severity IN ('urgent', 'review')")
    join = f"JOIN labels_ai l ON l.review_id = r.review_id AND l.run_id = '{LABEL_RUN}'" if needs_labels else ""
    return join, " AND ".join(clauses), params


def run(conn, intent, filters=None):
    """Returns (value, detail, review_ids). review_ids is filled when the set is small enough to cite."""
    join, where, params = _where(filters)
    base = f"FROM reviews r {join} WHERE {where}"
    if intent == "count_reviews":
        ids = [row[0] for row in conn.execute(f"SELECT r.review_id {base} ORDER BY r.review_id", params)]
        return len(ids), None, ids if len(ids) <= 20 else []
    if intent == "average_rating":
        avg, n = conn.execute(f"SELECT avg(r.rating), count(*) {base}", params).fetchone()
        return (round(avg, 2) if avg is not None else None), f"{n} reseñas", []
    if intent == "percent_with_comment":
        with_comment, n = conn.execute(
            f"SELECT sum(trim(coalesce(r.comment, '')) != ''), count(*) {base}", params).fetchone()
        return (round(100 * with_comment / n, 1) if n else None), f"{with_comment} de {n} reseñas", []
    if intent in ("top_employee", "top_month"):
        key = "r.employee" if intent == "top_employee" else "substr(r.created_at, 1, 7)"
        rows = conn.execute(f"SELECT {key}, count(*) AS n {base} GROUP BY 1 ORDER BY n DESC LIMIT 3", params).fetchall()
        if not rows:
            return None, None, []
        return rows[0][0], ", ".join(f"{k}: {n}" for k, n in rows), []
    raise ValueError(f"unknown intent: {intent}")


INTENTS = ["count_reviews", "average_rating", "percent_with_comment", "top_employee", "top_month"]
