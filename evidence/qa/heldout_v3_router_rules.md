# Q&A evaluation: questions_heldout.json (with relevance filter)

**Correct: 10/15** · invalid citations (S4): 0 · median latency 3806 ms

Meaning questions count as correct only if every required review is cited. Answers are not otherwise judged for wording.

| Q | Question | Route | Answer | Verdict |
|---|---|---|---|---|
| H01 | ¿Cuántas reseñas tuvo EMP_20 en agosto de 2026? | counting | 3. Reseñas: [R02696], [R02698], [R02716] | OK |
| H02 | ¿Cuál fue el promedio de calificación en marzo de 2026? | counting | 4.94 (462 reseñas) | OK |
| H03 | ¿Cuántas reseñas de 5 estrellas hubo en 2025? | counting | 255 | OK |
| H04 | ¿Qué empleado tuvo más reseñas en 2026? | counting | EMP_15 (EMP_15: 413, EMP_20: 356, EMP_16: 353) | OK |
| H05 | ¿Cuántas compras incluyeron llantas? | counting | 108 | OK |
| H06 | ¿Algún cliente se sintió acosado o incómodo con un empleado? | problems | "[El vendedor no me dio la mano, y me besó!! (Producto: Ycf allá) (Clasificación: urgente, conducta inapropiada) [R01301]" y "[Mala atención del vendedor, por decir y preguntar cosas acerca del casco. Es mi primera exper | cited 1/2; missing R00309 |
| H07 | ¿Algún cliente se quejó porque no le mostraron una talla? | problems | "[Le solicite una talla más grande de impermeable y no me lo quiso enseñar me dirigí para la otra sede y ay si me enseñaron la talla que le solicite a ella muchas gracias" [R02123] | OK |
| H08 | ¿Algún empleado le arregló algo a un cliente? | problems | No encontré reseñas sobre eso. | cited 0/1; missing R02740 |
| H09 | ¿Algún cliente pidió que le subieran el sueldo o ascendieran a un empleado? | general | No encontré reseñas sobre eso. | cited 0/3; missing R00855, R01086, R02913 |
| H10 | ¿Hay clientes que dijeron que volverían? | general | "Sí, hay clientes que dijeron que volverían. Un cliente comentó que 'volvería a comprar en este sitio' [R03100]." | cited 1/2; missing R02984 |
| H11 | ¿Qué dicen de los tintos y las aromáticas? | general | No encontré reseñas sobre eso. | cited 0/1; missing R02465 |
| H12 | ¿Algún cliente mencionó la navidad? | general | "Sus clientes mencionaron la navidad en la reseña [R00299]." | OK |
| H13 | ¿Hubo algún reclamo por un casco? | problems | "Se realiza reclamo y no dan solución de casco" [R02021] | OK |
| H14 | ¿Algún cliente dijo que lo atendieron mal en su primera visita? | problems | "Sí, varios clientes mencionaron problemas con la atención en su primera visita. Uno de ellos escribió: 'Mala atención del vendedor, por decir y preguntar cosas acerca del casco. Es mi primera experiencia en la tienda y  | OK |
| H15 | ¿Hay quejas sobre el parqueadero? | problems | No encontré reseñas sobre eso. | OK |
