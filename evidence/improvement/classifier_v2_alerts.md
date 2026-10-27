# Classifier run `v2`

Model: `qwen2.5:7b + alerts` · reviews scored: 1102

| Metric | Real | Synthetic | Held-out | Demo |
|---|---|---|---|---|
| n | 997 | 44 | 16 | 45 |
| S1 urgent recall | 4/4 | 15/17 | 8/8 | 20/21 |
| urgent flagged at least as review | 4/4 | 16/17 | 8/8 | 20/21 |
| S2 actionable recall | 14/14 | 29/32 | 12/12 | 44/45 |
| S3 actionable precision | 14/14 | 29/30 | 12/15 | 44/44 |
| theme correct (actionable, flagged) | 8/14 | 26/29 | 10/12 | 30/44 |
| exact severity | 996/997 | 39/44 | 12/16 | 34/45 |

Latency per review: median 797.0 ms, p90 1057 ms, total 14.0 min

## Errors on actionable decisions

| Review | Rating | Comment | Gold | Predicted | Model's reason |
|---|---|---|---|---|---|
| S0027 | 4 | el kasco shaf me queda apretao y no lo quicieron cambiar | urgent | review | Producto no ajusta y no se quieren hacer cambios |
| S0038 | 5 | Muy lindo el vendedor me preguntó si tenía novio jajaja | urgent | normal | Comentario sobre el vendedor |
| S0004 | 3 | Qué maravilla que nadie conteste el whatsapp | review | normal | Nadie contestó el WhatsApp |
| S0020 | 3 | meh | review | normal | Comentario neutro negativo |
| S0041 | 3 | El cliente no quiso esperar al técnico | normal | review | Cliente no quiso esperar al técnico |
| H0008 | 5 | Gracias al casco que me vendieron no me pasó nada en la caída, excelente producto | normal | review | Palabra de alerta: 'caida'. Modelo: Producto funcionó correctamente en una caída |
| H0009 | 5 | La garantía me la respondieron en un día, excelentes | normal | review | Palabra de alerta: 'garantia'. Modelo: Respuesta rápida a reclamo de garantía |
| H0010 | 5 | Me tocó esperar un poquito pero valió la pena | normal | review | Espera breve pero satisfactoria |
| D0039 | 5 | jaja todo excelente, sobre todo cuando se cayó el retrovisor que me instalaron 🙃 | urgent | normal | Chiste y elogio |
