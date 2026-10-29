"""Flow diagram PDF in English, as built (the Spanish `diagram_pdf.py` is the plan written before the code).
Usage: python -I scripts/diagram_pdf_en.py docs/diagrams/flow-diagram-en.pdf
"""
import sys

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from diagram_pdf import INK, STYLES, H, W, arrow, box, header


def legend(c):
    items = [("real", "Real client data"), ("data", "Local data"), ("dummy", "Synthetic data (dashed)"),
             ("code", "Python code"), ("local", "Embeddings (local)"), ("claude", "LLM: local Qwen (Claude optional)"),
             ("out", "Output for the owner")]
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


def page_preparation(c):
    header(c, "1. Data preparation",
           "Runs once (and when new reviews are imported). Everything runs on the PC: data, embeddings and LLM.", 1)

    top, h = 400, 105
    box(c, 30, top, 150, h, "real", "DynamoDB \"Rating\" (AWS)", [
        "Real client: 3,184 reviews", "Customer name and phone", "Never modified"], step=1)
    box(c, 210, top, 150, h, "code", "One-time export", [
        "Read-only scan", "Raw file kept outside the repo", "Owner's permission required"], step=2)
    box(c, 390, top, 170, h, "code", "Anonymization", [
        "Drops customer name and phone", "Employees -> EMP_xx", "Store/tablet -> pseudonyms",
        "Names in comments, misspellings too"], step=3)
    box(c, 600, top, 162, h, "data", "Local SQLite (reviews.db)", [
        "Anonymized reviews", "synthetic = 0 real, 1 hard, 2 held-out, 3 demo", "AI labels (step 5)"], step=4)

    arrow(c, [(180, top + h / 2), (210, top + h / 2)])
    arrow(c, [(360, top + h / 2), (390, top + h / 2)])
    arrow(c, [(560, top + h / 2), (600, top + h / 2)])

    box(c, 600, 215, 162, 120, "dummy", "Synthetic cases", [
        "44 hard cases (sarcasm, complaint + \"gracias\", 5★ hiding a problem, prompt injection)",
        "16 held-out, committed before tuning", "45 demo complaints, fictional staff"])
    arrow(c, [(681, 335), (681, top)], "synthetic = 1, 2, 3", dx=38)

    box(c, 320, 225, 220, 105, "claude", "Classification (local LLM)", [
        "Prompt written from CLAUDE.md", "Severity: normal / review / urgent, decided by the text",
        "Theme and a short reason", "+ alert words: raise severity, never lower it"], step=5)
    box(c, 320, 85, 220, 105, "local", "Embeddings (bge-m3, local)", [
        "Multilingual, runs on the PC via Ollama", "Each comment -> numbers that represent its meaning"], step=6)
    box(c, 40, 85, 220, 105, "data", "Vectors in SQLite", [
        "Stored next to the reviews", "Brute-force cosine search, under 1 s", "Chroma dropped: not needed at ~1,000",
        "(see page 2)"], step=7)

    arrow(c, [(590, top), (590, 278), (540, 278)], label_at=1)
    arrow(c, [(590, 278), (590, 138), (540, 138)])
    arrow(c, [(320, 250), (300, 250), (300, 372), (620, 372), (620, top)], "labels", label_at=1, dx=0, dy=-16, dashed=True)
    arrow(c, [(320, 138), (260, 138)])

    box(c, 40, 225, 220, 105, "note", "Privacy rules", [
        "Raw data never leaves the PC or enters Git",
        "The LLM runs locally (Ollama, Qwen 2.5 7B)",
        "Real and synthetic results reported separately",
        "Real-name check before every commit"])
    legend(c)


def page_questions(c):
    header(c, "2. Owner questions (\"ask your reviews\")",
           "Each question is routed: counts are answered by code; meaning questions use retrieval and the local LLM.", 2)

    box(c, 30, 370, 140, 90, "out", "Owner's question", ["Local web page", "(Streamlit)"], step=1)
    box(c, 200, 370, 160, 90, "code", "Router (rules first)", [
        "Count, problem or general?", "Filters kept only if the question's words support them"], step=2)
    arrow(c, [(170, 415), (200, 415)])

    box(c, 410, 445, 170, 85, "code", "Fixed SQL on SQLite", ["Counts, averages, rankings by employee, date, stars, product"], step="3a")
    box(c, 612, 445, 150, 85, "out", "Answer with numbers", ["Exact, lists the reviews", "No AI = nothing invented"], step="4a")
    arrow(c, [(360, 440), (385, 440), (385, 487), (410, 487)], "count", label_at=1, dx=-14, dy=0)
    arrow(c, [(580, 487), (612, 487)])

    box(c, 410, 310, 170, 95, "local", "Embed the question", ["Same bge-m3 model as page 1"], step="3b")
    box(c, 612, 310, 150, 95, "data", "Search the vectors", ["Top 20 + filters", "Problem questions: half the slots for flagged reviews"], step="4b")
    arrow(c, [(360, 395), (385, 395), (385, 357), (410, 357)], "meaning", label_at=2, dx=-7, dy=-11)
    arrow(c, [(580, 357), (612, 357)])

    box(c, 612, 160, 150, 110, "claude", "LLM (local Qwen)", [
        "Checks each review: relevant?", "Answers only from kept reviews, cites IDs"], step=5)
    arrow(c, [(687, 310), (687, 270)], "20 reviews", dx=28, dy=-2)
    box(c, 410, 160, 170, 110, "code", "Citation check", [
        "Every cited ID must be among the reviews given to the model", "If not: answer marked unverified"], step=6)
    arrow(c, [(612, 215), (580, 215)])
    box(c, 200, 160, 160, 110, "out", "Answer with evidence", [
        "Text + citations (R01972...)", "Cited review shown below"], step=7)
    arrow(c, [(410, 215), (360, 215)])

    box(c, 30, 40, 730, 95, "note", "Examples (real output, docs/demo.md)", [
        "\"¿Cuántas reseñas de 1 estrella hubo en 2026?\"  ->  count  ->  SQL  ->  11, listing every review",
        "\"¿Algún cliente tuvo un accidente o se cayó?\"  ->  problem  ->  finds R01972 (\"...despestañada y nos caimos\") with no word in common",
        "Known failure: \"¿Cuántas reseñas hubo en septiembre?\" (no year)  ->  month filter dropped  ->  3184 instead of 274",
    ])


def page_evaluation(c):
    header(c, "3. Evaluation, and the weekly digest that was cut",
           "The evaluation measures whether the system works. The weekly digest was planned and not built.", 3)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(INK)
    c.drawString(30, 505, "Evaluation (evidence for the submission)")
    y, h, w, gap = 370, 120, 165, 23
    xs = [30 + i * (w + gap) for i in range(4)]
    box(c, xs[0], y, w, h, "data", "Hand-labeled sets", [
        "997 real comments", "44 synthetic, 16 held-out (reported apart)",
        "25 + 15 questions with answer keys"], step=1)
    box(c, xs[1], y, w, h, "code", "Run both options", [
        "A: all 997 comments to the LLM", "B: retrieval (this design)", "Same 26 meaning questions"], step=2)
    box(c, xs[2], y, w, h, "code", "Metrics S1-S7", [
        "Urgent recall (target 100%)", "Actionable recall and precision", "Valid citations",
        "Accuracy, tokens and latency"], step=3)
    box(c, xs[3], y, w, h, "out", "Reports", [
        "evidence/eval_results.md", "Measured improvement and what got worse", "22 failing inputs with causes"], step=4)
    for i in range(3):
        arrow(c, [(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)])

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(INK)
    c.drawString(30, 315, "Weekly digest: planned, CUT (not built; see docs/effort.md)")
    y, h, w, gap = 200, 95, 128, 22
    xs = [30 + i * (w + gap) for i in range(5)]
    box(c, xs[0], y, w, h, "cut", "Trigger", ["\"Generate now\" button or every Monday"], step=1)
    box(c, xs[1], y, w, h, "cut", "Metrics (SQL)", ["This week vs last", "By employee and product"], step=2)
    box(c, xs[2], y, w, h, "cut", "Urgent + evidence", ["Reviews flagged urgent", "Evidence by theme"], step=3)
    box(c, xs[3], y, w, h, "cut", "LLM writes", ["Short summary", "What to act on first", "Recognitions"], step=4)
    box(c, xs[4], y, w, h, "cut", "Report", ["HTML / PDF", "Every claim cited"], step=5)
    for i in range(4):
        arrow(c, [(xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2)], color="#9A9A9A", dashed=True)

    box(c, 30, 45, 730, 120, "note", "Results against the definition of success (evidence/eval_results.md)", [
        "Urgent recall: real 4/4, held-out 8/8, synthetic 15/17. Actionable: real 14/14 found, 14/14 precise (no false alarms)",
        "Counting questions: 13/13 exact within the sets; months without a year are silently dropped (F17)",
        "Meaning questions: 7/16 dev, 5/10 held-out; the 7B model drops reviews retrieval found",
        "0 invalid citations in 40 answers. Full context (A) vs retrieval (B): 1/16 vs 7/16, 13 invented IDs vs 0",
    ])


def main(out):
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle("Calificapp Review Insights - Flow diagram (as built)")
    c.setAuthor("Santiago Molina")
    for draw in (page_preparation, page_questions, page_evaluation):
        draw(c)
        c.showPage()
    c.save()
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1])
