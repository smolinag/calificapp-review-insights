# Failure analysis

Specific inputs that break the prototype, on its own data, with the wrong output and the cause. Model: local `qwen2.5:7b` (temperature 0), classifier run `v2` (prompt v1 + alert words), router after commit `b60fc4e`.

Sources: classifier errors from `evidence/improvement/classifier_v2_alerts.md`; Q&A answers from `evidence/qa/qa_v3_router_rules.md` and `evidence/qa/heldout_v3_router_rules.md`; router and counting cases (F17–F21) reproduced directly on `router._grounded` / `stats.run`, without the model, so they are deterministic.

Severity of each failure for the owner: **high** = an urgent review is hidden or a number is silently wrong; **medium** = an answer is incomplete or misleading; **low** = noise.

## Summary

| # | Component | Input | Wrong output | Impact |
|---|---|---|---|---|
| F01 | Classifier | S0038 "Muy lindo el vendedor me preguntó si tenía novio jajaja" | `normal` (gold `urgent`) | high |
| F02 | Classifier | D0039 "jaja todo excelente, sobre todo cuando se cayó el retrovisor que me instalaron 🙃" | `normal` (gold `urgent`) | high |
| F03 | Classifier + alert words | S0027 "el kasco shaf me queda apretao y no lo quicieron cambiar" | `review` (gold `urgent`) | high |
| F04 | Classifier | S0004 "Qué maravilla que nadie conteste el whatsapp" | `normal` (gold `review`) | medium |
| F05 | Alert words | H0008 "Gracias al casco… no me pasó nada en la caída", H0009 "La garantía me la respondieron en un día" | `review` (gold `normal`) | low |
| F06 | Classifier | S0041 "El cliente no quiso esperar al técnico" (staff-written) | `review` (gold `normal`) | low |
| F07 | Classifier themes | R00933 "Muy buena atencion aunque precios altos"; R02123 (sizing complaint) | themes `otro` and `precio` | medium |
| F08 | Q&A answer step | Q12 "¿De qué se quejan los clientes sobre los precios?" | "No encontré reseñas…" although both reviews were retrieved | medium |
| F09 | Q&A relevance filter | H06 "¿Algún cliente se sintió acosado o incómodo con un empleado?" | Cites R01301, drops R00309 | high |
| F10 | Q&A answer step | Q15 "¿Hay quejas sobre las chicas del segundo piso?" | Cites R00309 instead of R01576 "las chicas de arriba" | medium |
| F11 | Q&A retrieval | Q14 recognitions; H09 "pidió que le subieran el sueldo" | 1/5 and 0/3 reviews cited | medium |
| F12 | Q&A relevance filter | H11 "¿Qué dicen de los tintos y las aromáticas?" | "No encontré reseñas…"; R02465 contains "tintos y aromáticas" | medium |
| F13 | Q&A answer step | Q13 "¿Algún cliente pidió que lo llamáramos?" | Correct review cited, plus R03023 misread as a call request | medium |
| F14 | Evaluation | Q13 (same answer) | Graded **OK** | medium |
| F15 | Q&A answer step | Q24 "…no supo atender por falta de experiencia?" | "No encontré reseñas…"; R03023 "Inesperto" is flagged `urgent` | medium |
| F16 | Counting route | Q25 "¿Cuántas quejas sobre precios hubo y cuáles son?" | "2" citing R00460, **R02123** | medium |
| F17 | Router filters | "¿Cuántas reseñas hubo en septiembre?" (no year) | **3184** (all reviews); September 2026 has 274 | high |
| F18 | Router filters | "¿Cuántas reseñas hubo la semana pasada?" | **3184** | high |
| F19 | Router filters | "¿Cuál es el promedio de EMP 15?" (space, no underscore) | Global average | high |
| F20 | Router intents | "¿Qué empleado tiene el promedio más bajo?" | One store-wide average, not a ranking | medium |
| F21 | Counting data | "¿Cuántas compras incluyeron llantas?" | 108; misses product "yanta" | low |
| F22 | Router rules | "¿Alguien quedó descontento?" / "¿Algún cliente agradeció la garantía?" | No rule matches / sent to complaint search | low |

## Classifier

**F01: personal remark by staff, light tone.** S0038 is a salesperson asking a customer whether they have a boyfriend, which `CLAUDE.md` defines as staff misconduct. The model's reason: "Comentario sobre el vendedor". Cause: the compliment ("muy lindo") and "jajaja" read as a positive joke, and the rule "a customer complimenting an employee's looks is `normal`" pulls the same way. No alert word covers "novio". The same pattern hid R00309 ("Pero muy morbosa") in v0 and v1 until a word was added for it (`evidence/improvement/README.md`).

**F02: sarcasm about a safety failure.** D0039 reports a mirror the store fitted that fell off, wrapped in praise and 🙃. Model reason: "Chiste y elogio". Cause: the model reads the tone, not the event. "se cayó" is not an alert word because it also appears in positive reviews ("Se me callo el cascoella me lo arreglo excelente servicio", R02740).

**F03: misspelling defeats both layers.** S0027 says the store refused to exchange a helmet that is too tight, which is an unresolved claim (`urgent`). The model calls it `review` ("Producto no ajusta y no se quieren hacer cambios"), and the alert pattern for refused exchanges expects "quisieron", not "quicieron". Real comments are full of such spellings ("exelente", "yantas", "Inesperto").

**F04: sarcasm without a marker.** S0004 has no emoji or contrast word; the model takes "Qué maravilla" at face value.

**F05: alert words without context.** "caída" and "garantía" also appear in praise. These two held-out cases are raised to `review`. Precision on held-out falls from 11/12 to 12/15. By design they are raised only to `review`, never `urgent`.

**F06: rule in `CLAUDE.md` not carried into the prompt.** `CLAUDE.md` says text written by staff is `normal`; the v1 prompt does not include that rule, so the model treats it as a customer complaint about waiting.

**F07: wrong themes on real reviews.** Severity is right for both (`review`), but themes are not: R00933 (price) is `otro`, and R02123 (a refused sizing, not a price issue) is `precio`. Theme accuracy on real actionable reviews is 8/14. F16 shows the effect.

## Q&A

**F08: retrieved but not answered.** For Q12 retrieval found both price complaints (recall 2/2, `evidence/retrieval/recall_labeled_k20.md`), but the answer is "No encontré reseñas sobre precios negativos…". Both reviews open with praise ("Excelente servicio pero faltó el descuento", "Muy buena atencion aunque precios altos"). Cause: the per-review relevance filter or the answer step reads them as praise.

**F09: the most important real case is dropped at the last step.** After the alert words, R00309 is classified `urgent` and labeled retrieval returns it for H06. The relevance filter then rejects it: "muy morbosa" does not say who was lewd to whom, and the 7B model does not connect it with "acosado o incómodo". The owner asking about harassment sees one case, not two.

**F10: wrong review for a paraphrase.** Q15 asks about "las chicas del segundo piso"; the review says "las chicas de arriba" (R01576, 1★). The answer instead cites R00309, which mentions neither, so a wrong citation looks verified: the citation check (C8) only confirms that the ID was retrieved, not that it supports the claim.

**F11: generic praise is invisible to similarity search.** Recognition requests are short and phrased many ways ("se merece asenso", "se merece el aumento 😘", "el empleado del mes"). Q14 is routed `general`; plain retrieval at k=20 finds 2/5 (`evidence/retrieval/recall_plain_k20.md`) and the answer cites 1/5. They are labeled `normal`, so labeled retrieval does not help either.

**F12: exact words, still missed.** R02465 "Me fasina la atención y los tintos y aromáticas🤪" contains both words of H11, and the answer is "No encontré reseñas sobre eso". Plain retrieval does return R02465 in the top 20 (checked with `retrieve.search`), so it is lost after retrieval: most likely the relevance filter rejects it as generic praise, the rule that also hurt Q16 (`evidence/qa/README.md`).

**F13: misread citation.** For Q13 the answer says two customers asked to be called and cites R03023 "Inesperto perditodo el debieron llamar otra persona para realizar su labor", where "llamar" means the store should have called another technician.

**F14: the evaluation accepts F13.** `scripts/eval_qa.py` marks a meaning question correct when every required review is cited; extra, wrong citations are not penalised. Q13 is therefore counted as OK. The Q&A scores in this repo are an upper bound on answer quality.

**F15: a flagged review is not connected to the question.** R03023 is classified `urgent` (theme `instalacion_taller`), and the question asks about lack of experience, but the answer is "No encontré reseñas sobre eso". Labeled retrieval returns R03023 in the top 20 (checked with `retrieve.search_labeled`), so it is lost at the relevance or answer step. The question says "el vendedor" while the review is about someone doing a job ("realizar su labor"), and "Inesperto" is misspelled.

## Counting and routing

**F16: a correct route that inherits the classifier's errors.** Q25 is correctly routed to counting with `theme = precio, actionable`. The SQL is exact, but the labels it filters on are wrong (F07), so the number is right by accident (2) and one cited review is wrong.

**F17: month without a year is silently dropped.** `router._grounded` keeps a month only if both the month name and the year appear in the question (a guard added because the model invented dates). "¿Cuántas reseñas hubo en septiembre?" therefore runs with no filter and answers **3184**, the count of all reviews, while September 2026 has 274. The UI shows a number with no warning. This breaks the S6 claim ("counting answered exactly") for any question phrased the way an owner would naturally phrase it.

**F18: relative dates are not supported.** "la semana pasada", "este mes", "ayer" produce no filter, and the answer is again 3184. The weekly digest (T17, not built) would need exactly this.

**F19: employee pseudonym must match `EMP_\d+` exactly.** "EMP 15" or "emp15" is not recognised, so the global average is returned as if it were the employee's. Related limitation: the real owner would ask by the employee's name, but only pseudonyms are in the data.

**F20: rankings exist only for review counts.** "¿Qué empleado tiene el promedio más bajo?" contains "promedio", so it is routed to `average_rating` and returns one store-wide number. "¿Qué empleado tiene peor calificación?" matches no counting rule and goes to retrieval, where the model sees 20 reviews out of 3184.

**F21: product is free text.** The count for "llantas" is a substring match on the product field; one product is typed "yanta" and is not counted. The answer key notes these counts are lower bounds.

**F22: word lists have edges.** "descontento" is not in the complaint list, so that question depends on the model's routing. "agradeció la garantía" is praise but contains "garantía", so it goes to the complaint search, which spends half its slots on flagged complaints.

## Patterns

1. **Tone over content.** F01, F02, F04, F08: the model trusts politeness, jokes and praise. This is the same failure the project exists to fix in the star rating (a 5★ can hide a complaint), reproduced one layer down.
2. **Word lists fix one phrasing at a time.** F03, F05, F22: the alert words and the router rules made measurable gains (`evidence/improvement/`, `evidence/qa/README.md`) but fail on misspellings and on the same word used positively.
3. **Silent defaults.** F17–F19: when a filter cannot be grounded it is dropped, and the system answers a broader question than the one asked, with no warning. A wrong number delivered with confidence is worse than "no entendí la fecha".
4. **Verification checks provenance, not support.** F10, F13, F14: citations always point to retrieved reviews (zero invalid citations in every run), but nothing checks that the cited review says what the answer claims, and the evaluation does not either.
5. **The last step loses what earlier steps found.** F08, F09, F15: retrieval and classification have the right reviews; the 7B model drops them at the relevance or answer step. `evidence/improvement/README.md` reaches the same conclusion and names a larger model as the next comparison.

## Not tested

- Prompt injection in the Q&A path: tested only in the classifier (S0024, fixed in v1). Q&A is asked only over real reviews, none of which contain instructions.
- Data the project did not choose: all reviews come from one store and one year; another store, city or product mix is untested.
- Claude as the model: supported through `LLM_PROVIDER=anthropic`, not measured.
