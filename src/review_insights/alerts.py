"""Safety net: alert words that raise a review's severity regardless of the model's label.

The model missed "Pero muy morbosa" (R00309) with and without context. For the cases that matter
most, a transparent word list does not depend on the model at all.
- strong words -> urgent: they almost only appear when something serious happened
- weak words   -> at least review: they also appear in positive reviews ("la garantía me la respondieron rápido")

Patterns are matched on lowercased text with accents removed.
"""
import re

from review_insights.anonymize import normalize

STRONG = {
    "conducta_inapropiada": [
        r"morbos[oa]s?", r"\bme beso\b", r"\bbeso\b", r"\bacos(o|aba|ador|adora)\b", r"manose",
        r"sin (mi )?permiso", r"mamacita|mamita|piropo",
        r"me (pidio|pidieron) (el |mi )?(numero|whats\w*|instagram|celular)",
    ],
    "instalacion_taller": [
        r"nos caimos|\bme cai\b", r"accidente", r"casi me (caigo|estrello|mato|accidento)", r"despesta[nñ]",
        r"se (solto|zafo|desprendio)", r"sin apretar|mal apretad", r"no fren(a|an|aba)\b",
    ],
    "garantia_reclamo": [
        r"superintendencia|demanda|denuncia", r"cobraron (dos veces|doble)", r"no me (entregaron|devolvieron)",
        r"no (me )?(quisieron|quiso) (cambiar|recibir|devolver)",
    ],
}
WEAK = [r"garantia", r"reclam", r"caida", r"incomod", r"\bflojo\b|\bfloja\b", r"\bfreno"]

_STRONG = [(theme, re.compile(p)) for theme, patterns in STRONG.items() for p in patterns]
_WEAK = [re.compile(p) for p in WEAK]


def check(text):
    """Returns (severity, theme, matched_text) for the strongest alert in the text, or None."""
    t = normalize(text or "")
    for theme, pattern in _STRONG:
        if m := pattern.search(t):
            return "urgent", theme, m.group()
    for pattern in _WEAK:
        if m := pattern.search(t):
            return "review", None, m.group()
    return None


RANK = {"normal": 0, "review": 1, "urgent": 2}


def apply(label, text):
    """Raises the label's severity if an alert word requires it; never lowers it."""
    alert = check(text)
    if not alert or RANK[alert[0]] <= RANK[label["severity"]]:
        return label
    severity, theme, word = alert
    return {**label, "severity": severity, "theme": theme or label["theme"],
            "reason": f"Palabra de alerta: '{word}'. Modelo: {label['reason']}"}
