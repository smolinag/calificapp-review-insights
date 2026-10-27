# Classifier run `v1`

Model: `qwen2.5:7b` · reviews scored: 1041

| Metric | Real | Synthetic |
|---|---|---|
| n | 997 | 44 |
| S1 urgent recall | 3/4 | 14/17 |
| urgent flagged at least as review | 3/4 | 16/17 |
| S2 actionable recall | 13/14 | 29/32 |
| S3 actionable precision | 13/13 | 29/30 |
| theme correct (actionable, flagged) | 7/13 | 25/29 |
| exact severity | 995/997 | 38/44 |

Latency per review: median 815 ms, p90 1059 ms, total 13.2 min

## Errors on actionable decisions

| Review | Rating | Comment | Gold | Predicted | Model's reason |
|---|---|---|---|---|---|
| R00309 | 5 | Excelente servicio Pero muy morbosa | urgent | normal | Comentario sexual no relacionado con el servicio |
| S0011 | 4 | Buena atención. El vendedor me pidió el número personal y me siguió escribiendo en la noch | urgent | review | Solicitar número personal y seguir escribiendo en la noche |
| S0027 | 4 | el kasco shaf me queda apretao y no lo quicieron cambiar | urgent | review | Producto no ajusta y no se quieren hacer cambios |
| S0038 | 5 | Muy lindo el vendedor me preguntó si tenía novio jajaja | urgent | normal | Comentario sobre el vendedor |
| S0004 | 3 | Qué maravilla que nadie conteste el whatsapp | review | normal | Nadie contestó el WhatsApp |
| S0020 | 3 | meh | review | normal | Comentario neutro negativo |
| S0041 | 3 | El cliente no quiso esperar al técnico | normal | review | Cliente no quiso esperar al técnico |
