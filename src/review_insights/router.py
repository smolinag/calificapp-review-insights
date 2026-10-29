"""Decides how to answer an owner's question.

Routes:
- counting: a number from fixed SQL (`stats`)
- problems: meaning question about complaints, incidents or requests -> labeled retrieval
- general:  any other meaning question -> plain retrieval

Whether a question is counting, and which query answers it, is decided by rules: a first version
that let the model decide sent "¿Hay quejas...?" questions to counting and misread "de 1 estrella".
Complaint and request words also decide problems by rule; the model extracts filters and chooses between
problems and general only for questions no rule covers.
"""
import json
import re

from review_insights import llm
from review_insights.classify import THEMES

COUNTING = re.compile(r"cu[aá]nt[oa]s|promedio|porcentaje|(qu[eé]|cu[aá]l).{0,40}\b(empleado|mes)\b.{0,40}\b(m[aá]s|menos)\b", re.I)
EMPLOYEE = re.compile(r"\bEMP_\d+\b", re.I)

SYSTEM = f"""You read questions from a store owner about customer reviews. Return only JSON.

"route": "problems" if the question is about complaints, incidents, claims, bad service, misconduct, accidents, or customers asking for something; otherwise "general".
"filters" (only those the question states):
  month: "YYYY-MM"; year: "YYYY"; rating: exact stars 1-5 ("de 1 estrella" means rating 1); max_rating: 1-5 ("menos de 4 estrellas" means max_rating 3);
  product_contains: one product word in singular ("casco", "llanta"); theme: one of {", ".join(THEMES)}, only if the question is about that topic;
  actionable: true if it asks about complaints or problems.
Months: enero=01, febrero=02, marzo=03, abril=04, mayo=05, junio=06, julio=07, agosto=08, septiembre=09, octubre=10, noviembre=11, diciembre=12.

Example: "¿Cuántas quejas de precio hubo en marzo de 2026?" -> {{"route": "problems", "filters": {{"month": "2026-03", "theme": "precio", "actionable": true}}}}
Example: "¿Qué opinan del parqueadero?" -> {{"route": "general", "filters": {{}}}}"""


def _intent(question):
    q = question.lower()
    if "promedio" in q:
        return "average_rating"
    if "porcentaje" in q:
        return "percent_with_comment"
    order = "bottom" if re.search(r"\bmenos\b", q) else "top"
    if not re.search(r"cu[aá]nt", q) and re.search(r"\bmes\b", q):
        return f"{order}_month"
    if not re.search(r"cu[aá]nt", q) and re.search(r"\bempleado\b", q):
        return f"{order}_employee"
    return "count_reviews"


MONTHS = {"01": "enero", "02": "febrero", "03": "marzo", "04": "abril", "05": "mayo", "06": "junio", "07": "julio",
          "08": "agosto", "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"}
# Questions about complaints, incidents or follow-up requests. These go to labeled retrieval whatever the
# model says: it sent "¿Algún cliente pidió que lo llamáramos?" and "¿Hay quejas sobre el parqueadero?" to general.
PROBLEM_WORDS = re.compile(
    r"quej|reclam|problem|\bmal[oa]?s?\b|groser|inapropiad|acos|inc[oó]mod|accident|se cay|garant[ií]a|devoluci"
    r"|insatisf|molest|demor|no supo|falta de experiencia|llam[aá]ramos|llamaran|llamen|nos llam|lo llam", re.I)
THEME_WORDS = {
    "precio": r"precio|caro|descuento", "tiempo_espera": r"esper|demor|tard", "garantia_reclamo": r"garant|reclam|cambio|devol",
    "conducta_inapropiada": r"inapropiad|acoso|conducta", "instalacion_taller": r"instalaci|taller|montaj",
    "producto_defecto": r"defect|dañ|da[ñn]ad", "asesoria_producto": r"asesor|talla|experiencia", "atencion": r"atenci|trato",
}


def _ratings(question):
    """Star filters parsed from the text: the model confused 'de 1 estrella' with 'at least 1'."""
    q = question.lower()
    if m := re.search(r"menos de (\d) estrellas?", q):
        return {"max_rating": int(m.group(1)) - 1}
    if m := re.search(r"m[aá]s de (\d) estrellas?", q):
        return {"min_rating": int(m.group(1)) + 1}
    if m := re.search(r"(?:de|con) (\d) estrellas?", q):
        return {"rating": int(m.group(1))}
    return {}


def _grounded(question, filters):
    """Keeps only filters the question's own words support; the model also invents filters."""
    q = question.lower()
    kept = {}
    month = str(filters.get("month", ""))
    if re.fullmatch(r"\d{4}-\d{2}", month) and MONTHS.get(month[5:]) in q and month[:4] in q:
        kept["month"] = month
    if str(filters.get("year", "")) and str(filters.get("year")) in q:
        kept["year"] = str(filters["year"])
    product = str(filters.get("product_contains", "")).lower()
    if product and not EMPLOYEE.search(product) and product.rstrip("s")[:5] in q:
        kept["product_contains"] = product
    if filters.get("actionable") and PROBLEM_WORDS.search(q):
        kept["actionable"] = True
    theme = filters.get("theme")
    if theme in THEME_WORDS and re.search(THEME_WORDS[theme], q):
        kept["theme"] = theme
    kept.update(_ratings(question))
    # the employee pseudonym is copied from the question, never taken from the model
    if match := EMPLOYEE.search(question):
        kept["employee"] = match.group().upper()
    return kept


def route(question):
    completion = llm.complete(f"Question: {question}", system=SYSTEM, json_mode=True, max_tokens=150)
    try:
        decision = json.loads(completion.text)
    except json.JSONDecodeError:
        decision = {}
    raw = {k: v for k, v in (decision.get("filters") or {}).items() if v not in (None, "", False)}
    filters = _grounded(question, raw)

    if COUNTING.search(question):
        result = {"route": "counting", "intent": _intent(question)}
    elif PROBLEM_WORDS.search(question):
        result = {"route": "problems"}
    else:
        result = {"route": decision.get("route") if decision.get("route") in ("problems", "general") else "general"}
    return {**result, "filters": filters, "latency_ms": completion.latency_ms}
