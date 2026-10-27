"""Flow diagram PDF for the Calificapp review-insights prototype.
Usage: python -I diagram_pdf.py <out.pdf>
"""
import math
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

W, H = landscape(letter)

STYLES = {
    "real":   ("#FBE1E1", "#B83B3B"),  # sensitive client data
    "data":   ("#DCEBFA", "#3B78C2"),
    "dummy":  ("#DCEBFA", "#3B78C2"),
    "code":   ("#EEEEEE", "#606060"),
    "local":  ("#ECE1F8", "#7A4FB5"),  # local small model
    "claude": ("#FCE6D6", "#C8642D"),
    "out":    ("#DDF2E3", "#2E8B57"),
    "note":   ("#FFF8DC", "#B8960C"),
}
INK = HexColor("#222222")
MUTED = HexColor("#555555")


def box(c, x, y, w, h, kind, title, lines=(), step=None):
    fill, stroke = STYLES[kind]
    c.setFillColor(HexColor(fill))
    c.setStrokeColor(HexColor(stroke))
    c.setLineWidth(1.4)
    c.setDash(4, 3) if kind == "dummy" else c.setDash()
    c.roundRect(x, y, w, h, 7, fill=1, stroke=1)
    c.setDash()
    pad = 8
    ty = y + h - 15
    if step:
        c.setFillColor(HexColor(stroke))
        c.circle(x + 13, ty + 3.5, 8, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(x + 13, ty + 0.5, str(step))
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 9.5)
    tx = x + (26 if step else pad)
    for i, t in enumerate(simpleSplit(title, "Helvetica-Bold", 9.5, w - (tx - x) - pad)):
        c.drawString(tx, ty - i * 11, t)
        last = ty - i * 11
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    yy = last - 13
    for line in lines:
        for j, t in enumerate(simpleSplit(line, "Helvetica", 8, w - 2 * pad - 6)):
            c.drawString(x + pad + (6 if j else 0), yy, ("• " if j == 0 else "") + t)
            yy -= 10


def arrow(c, pts, label=None, label_at=0, dx=0, dy=4, color="#444444", dashed=False):
    c.setStrokeColor(HexColor(color))
    c.setFillColor(HexColor(color))
    c.setLineWidth(1.3)
    c.setDash(3, 3) if dashed else c.setDash()
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p, stroke=1, fill=0)
    c.setDash()
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    a = math.atan2(y2 - y1, x2 - x1)
    s = 7
    head = c.beginPath()
    head.moveTo(x2, y2)
    head.lineTo(x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4))
    head.lineTo(x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4))
    head.close()
    c.drawPath(head, stroke=0, fill=1)
    if label:
        (ax, ay), (bx, by) = pts[label_at], pts[label_at + 1]
        c.setFont("Helvetica-Oblique", 7.5)
        c.setFillColor(HexColor("#333333"))
        for i, t in enumerate(label.split("\n")):
            c.drawCentredString((ax + bx) / 2 + dx, (ay + by) / 2 + dy - i * 9, t)


def header(c, title, subtitle, page):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(30, H - 40, title)
    c.setFont("Helvetica", 10)
    c.setFillColor(MUTED)
    c.drawString(30, H - 56, subtitle)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 30, H - 40, f"Calificapp · Review Insights · {page}/3")
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.line(30, H - 64, W - 30, H - 64)


def legend(c):
    items = [("real", "Datos reales del cliente"), ("data", "Datos locales"), ("dummy", "Datos dummy (borde punteado)"),
             ("code", "Código Python"), ("local", "Embeddings (local)"), ("claude", "LLM: Qwen local (Claude opcional)"),
             ("out", "Salida para el dueño")]
    x = 30
    c.setFont("Helvetica", 7.5)
    for kind, text in items:
        fill, stroke = STYLES[kind]
        c.setFillColor(HexColor(fill))
        c.setStrokeColor(HexColor(stroke))
        c.setDash(2, 2) if kind == "dummy" else c.setDash()
        c.roundRect(x, 18, 14, 10, 2, fill=1, stroke=1)
        c.setDash()
        c.setFillColor(INK)
        c.drawString(x + 18, 20.5, text)
        x += 18 + c.stringWidth(text, "Helvetica", 7.5) + 16


def page_preparacion(c):
    header(c, "1. Preparación de los datos",
           "Se ejecuta una vez (y al importar reseñas nuevas). Todo corre en el PC: datos, embeddings y LLM.", 1)

    top, h = 400, 105
    box(c, 30, top, 150, h, "real", "DynamoDB \"Rating\" (AWS)", [
        "Cliente real: ~3.244 reseñas", "Nombre y teléfono del cliente", "Nunca se modifica"], step=1)
    box(c, 210, top, 150, h, "code", "Exportación única", [
        "Scan de solo lectura", "Archivo crudo fuera del repo", "Requiere permiso del dueño"], step=2)
    box(c, 390, top, 170, h, "code", "Anonimización", [
        "Elimina nombre y teléfono", "Empleados -> EMP_xx", "Empresa/tablet -> seudónimos",
        "Revisión manual de nombres"], step=3)
    box(c, 600, top, 162, h, "data", "SQLite local (reviews.db)", [
        "Reseñas anonimizadas", "Columna synthetic = 0 / 1", "Etiquetas de la IA (paso 5)"], step=4)

    arrow(c, [(180, top + h / 2), (210, top + h / 2)])
    arrow(c, [(360, top + h / 2), (390, top + h / 2)])
    arrow(c, [(560, top + h / 2), (600, top + h / 2)])

    box(c, 600, 215, 162, 120, "dummy", "Casos difíciles dummy", [
        "44 casos, basados en patrones reales", "Sarcasmo, queja con \"gracias\"", "Problema grave en 5 estrellas",
        "Texto basura, prompt injection"])
    arrow(c, [(681, 335), (681, top)], "synthetic = 1", dx=30)

    box(c, 320, 225, 220, 105, "claude", "Clasificación (LLM local)", [
        "Tema: atención, producto, precio...", "Sentimiento", "Gravedad: normal / revisar / urgente",
        "Se guarda en SQLite"], step=5)
    box(c, 320, 85, 220, 105, "local", "Embeddings (modelo local)", [
        "Multilingüe, corre en el PC", "Cada comentario -> números que representan su significado"], step=6)
    box(c, 40, 85, 220, 105, "data", "Chroma (vector store local)", [
        "\"Mapa\" de significados", "Se usa para buscar por significado", "(ver página 2)"], step=7)

    arrow(c, [(590, top), (590, 278), (540, 278)], label_at=1)
    arrow(c, [(590, 278), (590, 138), (540, 138)])
    arrow(c, [(320, 250), (300, 250), (300, 372), (620, 372), (620, top)], "etiquetas", label_at=1, dx=0, dy=-16, dashed=True)
    arrow(c, [(320, 138), (260, 138)])

    box(c, 40, 225, 220, 105, "note", "Reglas de privacidad", [
        "Los datos crudos no salen del PC ni van a Git",
        "El LLM corre local (Ollama, Qwen 2.5 7B)",
        "Reales y dummy se reportan por separado"])
    legend(c)


def page_consulta(c):
    header(c, "2. Preguntas del dueño (\"pregúntale a tus reseñas\")",
           "Cada pregunta se enruta: los conteos los responde código normal; las preguntas de significado usan retrieval.", 2)

    box(c, 30, 370, 140, 90, "out", "Pregunta del dueño", ["Interfaz web local", "(Streamlit)"], step=1)
    box(c, 200, 370, 160, 90, "code", "Router", ["¿Pide números o significado?"], step=2)
    arrow(c, [(170, 415), (200, 415)])

    box(c, 410, 445, 170, 85, "code", "Consulta SQL a SQLite", ["Conteos y promedios por empleado, fecha o producto"], step="3a")
    box(c, 612, 445, 150, 85, "out", "Respuesta con números", ["Tabla o gráfico", "Sin IA = sin inventar"], step="4a")
    arrow(c, [(360, 440), (385, 440), (385, 487), (410, 487)], "conteo", label_at=1, dx=-14, dy=0)
    arrow(c, [(580, 487), (612, 487)])

    box(c, 410, 310, 170, 95, "local", "Embedding de la pregunta", ["Mismo modelo local de la página 1"], step="3b")
    box(c, 612, 310, 150, 95, "data", "Buscar en Chroma", ["Top 20 más cercanos", "+ filtros (empleado, fechas)"], step="4b")
    arrow(c, [(360, 395), (385, 395), (385, 357), (410, 357)], "significado", label_at=1, dx=-20, dy=0)
    arrow(c, [(580, 357), (612, 357)])

    box(c, 612, 160, 150, 110, "claude", "LLM (Qwen local)", [
        "Pregunta + 20 reseñas", "Responde solo con esas reseñas y cita los IDs"], step=5)
    arrow(c, [(687, 310), (687, 270)], "20 reseñas", dx=28, dy=-2)
    box(c, 410, 160, 170, 110, "code", "Verificación de citas", [
        "Cada ID citado debe estar entre los 20 recuperados", "Si no: se marca la respuesta"], step=6)
    arrow(c, [(612, 215), (580, 215)])
    box(c, 200, 160, 160, 110, "out", "Respuesta con evidencia", [
        "Texto + citas (R01972...)", "Clic para ver la reseña"], step=7)
    arrow(c, [(410, 215), (360, 215)])

    box(c, 30, 40, 730, 95, "note", "Ejemplos", [
        "\"¿Cuántas reseñas de 1 estrella hubo en septiembre?\"  ->  conteo  ->  SQL  ->  3",
        "\"¿Algún cliente tuvo un accidente?\"  ->  significado  ->  retrieval encuentra R01972 (\"...nos caímos\") aunque no comparte palabras con la pregunta",
        "Falla conocida: \"...no me lo quiso enseñar... en la otra sede sí... muchas gracias\" puede quedar cerca de los elogios y no aparecer al buscar quejas",
    ])


def page_reporte(c):
    header(c, "3. Reporte semanal y evaluación",
           "El reporte llega al dueño sin que tenga que preguntar. La evaluación mide si el sistema realmente funciona.", 3)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(INK)
    c.drawString(30, 505, "Reporte semanal")
    y, h, w, gap = 370, 120, 128, 22
    xs = [30 + i * (w + gap) for i in range(5)]
    box(c, xs[0], y, w, h, "code", "Disparador", ["Botón \"Generar ahora\" o tarea programada cada lunes"], step=1)
    box(c, xs[1], y, w, h, "code", "Métricas (SQL)", ["Semana vs anterior", "Por empleado y producto", "Calculadas, no inventadas"], step=2)
    box(c, xs[2], y, w, h, "data", "Urgentes + evidencia", ["Reseñas \"urgente\" (paso 5 de la página 1)", "Retrieval de evidencia por tema"], step=3)
    box(c, xs[3], y, w, h, "claude", "LLM redacta", ["Resumen corto", "Qué atender primero", "Reconocimientos"], step=4)
    box(c, xs[4], y, w, h, "out", "Reporte", ["HTML / PDF", "Cada afirmación con su ID", "Citas verificadas"], step=5)
    for i in range(4):
        arrow(c, [(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(INK)
    c.drawString(30, 315, "Evaluación (evidencia para la entrega)")
    y, h, w, gap = 165, 130, 165, 23
    xs = [30 + i * (w + gap) for i in range(4)]
    box(c, xs[0], y, w, h, "data", "Set etiquetado a mano", [
        "Todas las reseñas con comentario", "Gravedad y tema correctos", "Reales y dummy por separado",
        "~25 preguntas con respuesta"], step=1)
    box(c, xs[1], y, w, h, "code", "Correr las dos opciones", [
        "A: mandar todo al LLM", "B: retrieval (este diseño)", "Mismas preguntas"], step=2)
    box(c, xs[2], y, w, h, "code", "Métricas", [
        "Recall de urgentes (meta 100%)", "Precisión de alertas", "Citas válidas",
        "Latencia (y costo si se usa Claude)"], step=3)
    box(c, xs[3], y, w, h, "out", "Informe", [
        "Mejora medida: antes / después", "Qué empeoró", "Fallas con inputs concretos"], step=4)
    for i in range(3):
        arrow(c, [(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])

    box(c, 30, 45, 730, 90, "note", "Qué cuenta como éxito", [
        "Ninguna reseña grave sin detectar (ej. R01972 caída por llanta, R00309 queja dentro de 5 estrellas)",
        "Cero citas inventadas en respuestas y reportes",
        "Retrieval más barato y rápido que mandar todo, reportando dónde es peor (preguntas de conteo -> SQL)",
    ])


def main(out):
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle("Calificapp Review Insights - Diagrama de flujo")
    c.setAuthor("Santiago Molina")
    for draw in (page_preparacion, page_consulta, page_reporte):
        draw(c)
        c.showPage()
    c.save()
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1])
