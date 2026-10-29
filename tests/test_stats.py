"""Fixed SQL behind counting questions, on a small in-memory database."""
import pytest

from review_insights import stats
from review_insights.db import connect


@pytest.fixture
def conn():
    conn = connect(":memory:")
    rows = [  # employee, created_at, rating, synthetic
        ("EMP_01", "2026-05-02", 5, 0), ("EMP_01", "2026-05-09", 4, 0), ("EMP_01", "2026-06-01", 5, 0),
        ("EMP_02", "2026-06-03", 1, 0), ("EMP_02", "2026-06-04", 5, 0),
        ("EMP_03", "2026-06-05", 5, 0),
        ("EMP_03", "2026-06-06", 1, 1),  # synthetic: never counted
    ]
    conn.executemany("INSERT INTO reviews (review_id, employee, created_at, rating, synthetic) VALUES (?, ?, ?, ?, ?)",
                     [(f"R{i:05d}", *row) for i, row in enumerate(rows, 1)])
    return conn


def test_top_and_bottom_employee(conn):
    assert stats.run(conn, "top_employee")[0] == "EMP_01"
    assert stats.run(conn, "bottom_employee")[0] == "EMP_03"


def test_top_and_bottom_month(conn):
    assert stats.run(conn, "top_month")[0] == "2026-06"
    assert stats.run(conn, "bottom_month")[0] == "2026-05"


def test_count_with_filters_cites_the_reviews(conn):
    assert stats.run(conn, "count_reviews", {"rating": 1}) == (1, None, ["R00004"])
    assert stats.run(conn, "count_reviews", {"month": "2026-06", "employee": "emp_01"})[0] == 1


def test_average_ignores_synthetic_reviews(conn):
    assert stats.run(conn, "average_rating", {"employee": "EMP_03"})[0] == 5
