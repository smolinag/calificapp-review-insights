# S7: full context (A) vs retrieval (B), meaning questions

Model: `qwen2.5:7b` · A: all 997 real comments in one prompt (num_ctx 32768) · B: `answer.ask` (router, retrieval k=20, relevance filter, answer). Same session, same GPU.

| Mode | Correct | Median latency | Median input tokens per question | Invalid citations |
|---|---|---|---|---|
| A full context | questions: 1/16 · questions_heldout: 1/10 | 33183.5 ms | 17986.5 | 13 |
| B retrieval | questions: 7/16 · questions_heldout: 6/10 | 28325.5 ms | 5629.0 | 0 |

| Q | Question | A | B | Latency ms A / B | Input tokens A / B |
|---|---|---|---|---|---|
| Q09 | ¿Algún cliente tuvo un accidente o se cayó? | cited 0/1 | OK | 766 / 28087 | 17988 / 5681 (22 calls) |
| Q10 | ¿Hay quejas de comportamiento inapropiado de algún empleado? | cited 0/2 | OK | 36791 / 24108 | 17988 / 5907 (22 calls) |
| Q11 | ¿Qué reclamos de garantía siguen sin resolver? | cited 0/1 | OK | 25169 / 39884 | 17985 / 5734 (22 calls) |
| Q12 | ¿De qué se quejan los clientes sobre los precios? | cited 0/2 | cited 0/2 | 39046 / 21343 | 17985 / 5801 (22 calls) |
| Q13 | ¿Algún cliente pidió que lo llamáramos? | cited 0/1 | OK | 26722 / 31269 | 17987 / 5747 (22 calls) |
| Q14 | ¿Qué empleados merecen un reconocimiento según los clientes? | cited 0/5 | cited 1/5 | 60291 / 28369 | 17986 / 5403 (22 calls) |
| Q15 | ¿Hay quejas sobre las chicas del segundo piso? | cited 0/1 | cited 0/1 | 45697 / 23782 | 17985 / 5634 (22 calls) |
| Q16 | ¿Qué opinan los clientes del café y las bebidas? | cited 0/3 | cited 1/3 | 33037 / 22454 | 17986 / 5392 (22 calls) |
| Q17 | ¿Algún cliente habló de la atención por WhatsApp o virtual? | cited 0/2 | OK | 36789 / 28199 | 17988 / 5477 (22 calls) |
| Q18 | ¿Hay clientes que pusieron buena calificación pero se quejaron de algo? | cited 0/3 | cited 2/3 | 33330 / 35606 | 17990 / 5818 (22 calls) |
| Q19 | ¿Hubo problemas con llantas? | cited 0/1 | OK | 37760 / 23676 | 17981 / 5624 (22 calls) |
| Q20 | ¿Algún cliente comparó con otra sede? | cited 0/1 | OK | 30889 / 24892 | 17983 / 5406 (22 calls) |
| Q21 | ¿Hay quejas por tiempos de espera? | OK | cited reviews when none apply | 31825 / 34744 | 17984 / 5591 (22 calls) |
| Q22 | ¿Algún empleado fue grosero o atendió mal? | cited 0/3 | cited 1/3 | 30872 / 28282 | 17987 / 5902 (22 calls) |
| Q23 | ¿Qué dicen los clientes de la instalación y el taller? | cited 0/2 | cited 1/2 | 53898 / 27298 | 17987 / 5671 (22 calls) |
| Q24 | ¿Hay clientes que el vendedor no supo atender por falta de experiencia? | cited 0/1 | cited 0/1 | 33566 / 20231 | 17990 / 5416 (21 calls) |
| H06 | ¿Algún cliente se sintió acosado o incómodo con un empleado? | cited 0/2 | cited 1/2 | 52386 / 28394 | 17990 / 5885 (22 calls) |
| H07 | ¿Algún cliente se quejó porque no le mostraron una talla? | cited 0/1 | OK | 34016 / 34480 | 17990 / 5856 (22 calls) |
| H08 | ¿Algún empleado le arregló algo a un cliente? | cited 0/1 | cited 0/1 | 32800 / 32351 | 17987 / 5295 (21 calls) |
| H09 | ¿Algún cliente pidió que le subieran el sueldo o ascendieran a un empleado? | cited 0/3 | cited 0/3 | 32959 / 29709 | 17994 / 5367 (21 calls) |
| H10 | ¿Hay clientes que dijeron que volverían? | cited 0/2 | cited 1/2 | 54841 / 27612 | 17984 / 5361 (22 calls) |
| H11 | ¿Qué dicen de los tintos y las aromáticas? | cited 0/1 | OK | 39259 / 28587 | 17986 / 5517 (22 calls) |
| H12 | ¿Algún cliente mencionó la navidad? | cited 0/1 | OK | 30640 / 29481 | 17984 / 5344 (22 calls) |
| H13 | ¿Hubo algún reclamo por un casco? | cited 0/1 | OK | 31278 / 29912 | 17984 / 5869 (22 calls) |
| H14 | ¿Algún cliente dijo que lo atendieron mal en su primera visita? | cited 0/1 | OK | 29939 / 31824 | 17989 / 5821 (22 calls) |
| H15 | ¿Hay quejas sobre el parqueadero? | OK | OK | 28489 / 26996 | 17983 / 5264 (21 calls) |
