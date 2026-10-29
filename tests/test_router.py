"""Router rules. The model is stubbed: these tests check what the rules decide, without Ollama."""
import json

import pytest

from review_insights import llm, router


def stub_model(monkeypatch, route="general", filters=None):
    reply = json.dumps({"route": route, "filters": filters or {}})
    monkeypatch.setattr(llm, "complete", lambda *a, **k: llm.Completion(reply, "stub", None, None, 0))


@pytest.mark.parametrize("question, intent", [
    ("¿Cuántas reseñas hubo en julio de 2026?", "count_reviews"),
    ("¿cuantos clientes dejaron comentario?", "count_reviews"),
    ("¿Cuál es el promedio de EMP_07?", "average_rating"),
    ("¿Qué porcentaje de clientes escribió algo?", "percent_with_comment"),
    ("¿Qué empleado tuvo más reseñas?", "top_employee"),
    ("¿Qué empleado tuvo menos reseñas?", "bottom_employee"),
    ("¿Cuál fue el mes con menos calificaciones?", "bottom_month"),
    ("¿Cuántas quejas de precio hubo y cuáles?", "count_reviews"),
])
def test_counting_questions_are_decided_by_rules(monkeypatch, question, intent):
    stub_model(monkeypatch, route="problems")  # the model's opinion must not matter
    decision = router.route(question)
    assert decision["route"] == "counting"
    assert decision["intent"] == intent


@pytest.mark.parametrize("question", [
    "¿Algún cliente pidió que lo llamaran cuando llegara el producto?",
    "¿Hay quejas sobre el baño?",
    "¿Alguien dijo que lo atendieron mal?",
    "¿Hubo reclamos por impermeables?",
    "¿Algún cliente se sintió incómodo?",
    "¿Algún técnico no supo hacer el trabajo?",
])
def test_complaint_and_request_questions_go_to_problems_even_if_model_says_general(monkeypatch, question):
    stub_model(monkeypatch, route="general")
    assert router.route(question)["route"] == "problems"


@pytest.mark.parametrize("question", ["¿Qué opinan del parqueadero?", "¿Alguien habló de la música?"])
def test_other_meaning_questions_follow_the_model(monkeypatch, question):
    stub_model(monkeypatch, route="general")
    assert router.route(question)["route"] == "general"
    stub_model(monkeypatch, route="problems")
    assert router.route(question)["route"] == "problems"


def test_invalid_model_output_falls_back_to_general(monkeypatch):
    monkeypatch.setattr(llm, "complete", lambda *a, **k: llm.Completion("not json", "stub", None, None, 0))
    assert router.route("¿Qué dicen de los guantes?") == {"route": "general", "filters": {}, "latency_ms": 0}


@pytest.mark.parametrize("question, expected", [
    ("¿Cuántas reseñas de 1 estrella hubo?", {"rating": 1}),
    ("¿Cuántas reseñas con menos de 4 estrellas hay?", {"max_rating": 3}),
    ("¿Cuántas reseñas con más de 3 estrellas hay?", {"min_rating": 4}),
])
def test_star_filters_come_from_the_text_not_the_model(monkeypatch, question, expected):
    stub_model(monkeypatch, filters={"rating": 5, "min_rating": 1})
    assert router.route(question)["filters"] == expected


def test_filters_the_question_does_not_support_are_dropped(monkeypatch):
    invented = {"month": "2026-05", "year": "2025", "product_contains": "llanta", "theme": "precio", "actionable": True}
    stub_model(monkeypatch, filters=invented)
    assert router.route("¿Qué opinan del servicio?")["filters"] == {}


def test_supported_filters_are_kept(monkeypatch):
    stub_model(monkeypatch, filters={"month": "2026-05", "product_contains": "llanta", "theme": "precio",
                                     "actionable": True})
    filters = router.route("¿Cuántas quejas de precio de llantas hubo en mayo de 2026?")["filters"]
    assert filters == {"month": "2026-05", "product_contains": "llanta", "theme": "precio", "actionable": True}


def test_employee_is_copied_from_the_question(monkeypatch):
    stub_model(monkeypatch, filters={"employee": "EMP_99"})
    assert router.route("¿Cuántas reseñas tiene emp_07?")["filters"] == {"employee": "EMP_07"}
