"""Web page for the store owner.

Run from the repo root: .venv/Scripts/streamlit run src/review_insights/app.py
"""
import streamlit as st

from review_insights.answer import ask
from review_insights.db import connect
from review_insights.stats import LABEL_RUN

SEVERITY = {"urgent": ("🔴", "Urgente"), "review": ("🟡", "Para revisar")}

st.set_page_config(page_title="Calificapp · Reseñas", page_icon="⭐", layout="wide")
conn = connect()  # one connection per rerun: sqlite connections can't cross Streamlit's threads


def review_card(r, label=None):
    stars = "★" * r["rating"] + "☆" * (5 - r["rating"])
    st.markdown(f"**{r['review_id']}** · {r['created_at'][:10]} · {stars} · {r['employee']}")
    st.markdown(f"> {' '.join((r['comment'] or '').split())}")
    if (r["product"] or "").strip():
        st.caption(f"Producto: {r['product'].strip()}")
    if label:
        st.caption(f"Motivo: {label}")


st.title("Calificapp · Reseñas")

total, avg, commented = conn.execute(
    "SELECT count(*), avg(rating), sum(trim(coalesce(comment, '')) != '') FROM reviews WHERE synthetic = 0").fetchone()
flagged = conn.execute(
    """SELECT r.*, l.severity, l.theme, l.reason FROM labels_ai l JOIN reviews r USING (review_id)
       WHERE l.run_id = ? AND r.synthetic = 0 AND l.severity IN ('urgent', 'review')
       ORDER BY l.severity = 'urgent' DESC, r.created_at DESC""", (LABEL_RUN,)).fetchall()
urgent = sum(r["severity"] == "urgent" for r in flagged)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Reseñas", f"{total:,}".replace(",", "."))
c2.metric("Calificación promedio", f"{avg:.2f} ★")
c3.metric("Con comentario", f"{commented / total:.0%}")
c4.metric("Para atender", f"{len(flagged)}", f"{urgent} urgentes", delta_color="inverse")

ask_tab, flagged_tab = st.tabs(["💬 Pregúntale a tus reseñas", "🚩 Atender primero"])

with ask_tab:
    st.caption("Ejemplos: ¿Algún cliente tuvo un accidente? · ¿Cuántas reseñas de 1 estrella hubo en 2026? · "
               "¿Qué dicen de los cascos?")
    with st.form("ask"):
        question = st.text_input("Tu pregunta", placeholder="¿De qué se quejan los clientes?")
        submitted = st.form_submit_button("Preguntar")
    if submitted and question.strip():
        with st.spinner("Buscando en las reseñas… (puede tardar unos segundos)"):
            result = ask(conn, question.strip())
        route = {"counting": "Conteo exacto sobre los datos", "problems": "Búsqueda de problemas",
                 "general": "Búsqueda por significado"}[result["route"]]
        st.caption(f"{route} · {result['latency_ms'] / 1000:.1f} s")
        st.markdown(result["answer"])
        if not result["verified"]:
            st.warning(f"La respuesta cita reseñas que no se le entregaron: {', '.join(result['invalid_citations'])}. "
                       "No confíes en esas partes.")
        if result["citations"]:
            st.subheader("Reseñas citadas")
            placeholders = ", ".join("?" * len(result["citations"]))
            for r in conn.execute(f"SELECT * FROM reviews WHERE review_id IN ({placeholders}) ORDER BY created_at DESC",
                                  result["citations"]):
                with st.container(border=True):
                    review_card(r)

with flagged_tab:
    st.caption("Reseñas que la IA o las palabras de alerta marcaron. Revisa el motivo: puede haber falsas alarmas.")
    for r in flagged:
        icon, name = SEVERITY[r["severity"]]
        with st.container(border=True):
            st.markdown(f"{icon} **{name}** · {r['theme'].replace('_', ' ')}")
            review_card(r, r["reason"])
