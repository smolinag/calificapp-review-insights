# Demo transcript

Output of the real pipeline on 2026-10-29, on the anonymized real reviews (demo reviews off), local model `qwen2.5:7b`, classifier run `v2`, router after `b60fc4e`. Produced by calling `answer.ask` for each question; the web page (`streamlit run src/review_insights/app.py`) shows the same answers. Narration in *italics*; everything else is verbatim output. Latencies are from a cold start right after another evaluation; in normal use meaning questions take ~4 s.

*The owner sees an average of 4.9★ every month. The page opens with the list of reviews to act on first, chosen by reading the text, not the stars.*

## 1. Atender primero (reseñas reales marcadas como urgentes)

- **R03023** · 1★ · instalacion_taller: “Inesperto perditodo el debieron llamar otra persona para realizar su labor” — motivo: Trabajo realizado por persona inexperta
- **R02021** · 1★ · garantia_reclamo: “Se realiza reclamo y no dan solución de casco” — motivo: Reclamo sin solución
- **R01972** · 1★ · producto_defecto: “Me monto una llanta que paresento una despestañada y nos caimos” — motivo: Llanta presentaba despestañada y se produjo caída
- **R01301** · 1★ · conducta_inapropiada: “El vendedor no me dió la mano , y me besó!! 💋” — motivo: Besó al cliente sin permiso
- **R00309** · 5★ · conducta_inapropiada: “Excelente servicio Pero muy morbosa” — motivo: Palabra de alerta: 'morbosa'. Modelo: Comentario sexual no relacionado con el servicio

*One 5★ review is on this list: "Excelente servicio. Pero muy morbosa". The model alone called it unrelated to the service; the alert word "morbosa" raised it (`evidence/improvement/README.md`). R03023 is over-escalated: the gold label is `review` (inexperienced technician, no safety incident), but the rule is "when in doubt, choose the higher level".*

*Now the owner asks questions in plain Spanish.*

## 2. ¿Algún cliente tuvo un accidente o se cayó?

Ruta: `problems` · filtros: `{'actionable': True}` · 10.0 s · citas: ['R01972'] · inválidas: []

> "[Me monté una llanta que presentaba una despestañada y nos caímos]" [R01972]

*Good case: the review says "despestañada" (tyre bead off the rim) and "nos caimos", not "accidente". The router sends complaint questions to the search that prioritises flagged reviews.*

## 3. ¿Cuántas reseñas de 1 estrella hubo en 2026?

Ruta: `counting` · filtros: `{'year': '2026', 'rating': 1}` · 1.0 s · citas: ['R00355', 'R01301', 'R01576', 'R01851', 'R01972', 'R02020', 'R02021', 'R02123', 'R02838', 'R03023', 'R03045'] · inválidas: []

> 11. Reseñas: [R00355], [R01301], [R01576], [R01851], [R01972], [R02020], [R02021], [R02123], [R02838], [R03023], [R03045]

*Good case: counting questions are answered by SQL, not the model, so the number is exact and every review is listed.*

## 4. ¿Algún cliente se sintió acosado o incómodo con un empleado?

Ruta: `problems` · filtros: `{'actionable': True}` · 12.4 s · citas: ['R01301', 'R02838'] · inválidas: []

> "[El vendedor no me dio la mano, y me besó!! (Producto: Ycf allá)] [R01301]" y "[Mala atención del vendedor, por decir y preguntar cosas acerca del casco. Es mi primera experiencia en la tienda y es muy mala por parte de su asesira (Producto: Casco)] [R02838]" mencionan situaciones donde los clientes se sintieron incómodos con los empleados, aunque no se especifica que se sintieran exactamente acosados.

*Partial: R01301 is found, but R00309 ("muy morbosa"), the case from the first list, is dropped by the model at the last step, and R02838 (a rude salesperson) is offered instead. The answer itself admits it is not exactly harassment (`docs/failure-analysis.md` F09).*

## 5. ¿Qué dicen de los tintos y las aromáticas?

Ruta: `general` · filtros: `{}` · 7.6 s · citas: [] · inválidas: []

> No encontré reseñas sobre eso.

*Bad case: review R02465 says "Me fasina la atención y los tintos y aromáticas🤪". Search retrieves it, and the model's relevance check discards it as generic praise. "No encontré" means "not found", not "there are none" (F12).*

## 6. ¿Cuántas reseñas hubo en septiembre?

Ruta: `counting` · filtros: `{}` · 0.7 s · citas: [] · inválidas: []

> 3184

*Bad case, the worst one: September 2026 had 274 reviews. The question has no year, the router drops the month filter it cannot ground, and SQL counts all 3,184 reviews. The number looks exact and comes with no warning (F17).*
