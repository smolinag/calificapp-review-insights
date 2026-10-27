# 2. Data provenance

## Source

| | |
|---|---|
| System | Calificapp backend (`service-rater` Serverless stack), AWS `us-east-1` |
| Table | DynamoDB `Rating` — partition key `id` (company), sort key `rangeId` (`YYYY-MM-DD-{deviceId}-{timestamp}`) |
| How written | `POST /rating` Lambda, one item per rating submitted on a store tablet |
| Export | One read-only `scan` on **2026-10-20**. Nothing in DynamoDB was modified. |
| Size | 3,244 items, 2025-08-05 → 2026-10-20 |
| Client permission | **Granted 2026-10-27** by the store owner, for anonymized use in this prototype and its evaluation. |

## Fields

| Field | Used? | Notes |
|---|---|---|
| `rating` | Yes | 1–5 (validated by the backend) |
| `comment` | Yes | Optional free text — the main input for the AI |
| `product` | Yes | Optional free text ("casco", "cascos", "casco mt"...) |
| `employeeName` | Pseudonymized | Stored as a name string, not an ID |
| `createdAt`, `rangeId` | Yes | Date and time |
| `deviceId`, `deviceAlias` | Pseudonymized | Which tablet |
| `ratingTimeMs` | Yes | Time spent rating (median 17 s) |
| `raterName`, `raterPhone` | **Dropped** | Customer personal data; only "was provided: yes/no" is kept |
| `ttl` | Dropped | Items expire 500 days after creation |

## What the data represents

- **One store.** 3,184 of 3,244 reviews (98%) come from a single motorcycle-gear store with 23 employees and 3 tablets.
- **Spanish only.** Informal, frequent misspellings ("exelente atencion"), some emoji (75 comments). 2 comments contain any English.
- **Mostly praise.** Rating distribution: 1★ 14 · 2★ 6 · 3★ 18 · 4★ 195 · 5★ 3,011.
- **Short comments.** 1,024 reviews (32%) have a comment; median 18 characters, 90th percentile 44, max 182. Only 79 are ≥ 50 characters.
- **Few negatives, but real ones.** ~15–20 genuinely actionable comments in the real data (see the problem statement).

## What it does not represent

- **Customers who did not rate.** The tablet is at the counter, often with the employee present. This likely inflates ratings and suppresses complaints; the data cannot measure by how much.
- **Other stores or industries.** Results are not evidence the approach works for, e.g., a restaurant or a clinic.
- **History older than ~16 months**: removed by the 500-day TTL.
- **Unique employee identity.** Employees are stored by name, so a renamed employee splits into two, and two employees with the same name merge.

## Known quirks and limitations

1. **Test data.** The other company in the table (60 reviews, Aug 2025 – Mar 2026) contains keyboard mashing ("Jfjjfjgg") and sports-team test ratings ("Jugó regular"). **Excluded** from the dataset.
2. **Rating-scale change.** Between ~2026-01-30 and ~2026-03-07 the app showed 3 options (sent as 1, 3, 5) instead of 5. Values stay on the same scale, but 2s and 4s are under-represented in that window. Tablets switch builds at different times, so the window is approximate.
3. **Rating/comment mismatch.** A 5★ can carry a serious complaint (R00309) and a 1★ can end in "muchas gracias" (R02123). The rating alone is not a reliable signal.
4. **Third-person / staff-written comments.** Some comments read as if written by an employee ("No le gustó la hora para prestar el servicio", R02412).
5. **Name field misused.** Many customers typed "Excelente" or "Bueno" into the *name* field, so `has_rater_name` overstates how many customers left their name.
6. **Comment about a different employee.** Some comments praise someone other than the employee selected on the tablet (R01351 is rated for EMP_19 and asks for recognition for EMP_21). Per-employee results inherit this noise.
7. **Employees registered twice.** Three people appear both by first name alone and with a surname (17 + 396 reviews, 10 + 1, 334 + 1). The owner confirmed they are the same person, so each pair is merged into one pseudonym (23 registered names → 20 employees). The alias list is private (`data/raw/employee_aliases_PRIVATE.json`).
8. **Non-employee names in comments.** One comment (R01676) names a person who is not a registered employee. The owner asked for it to be removed; it becomes `[NOMBRE]`.
9. **Reference labels drafted by Claude.** The gold labels (`data/labels_gold.csv`) were drafted by Claude Opus after reading every comment, with the reason for each non-trivial label in `scripts/build_gold_labels.py`. They have one annotator and no agreement measure, and when Claude is the classifier under test, shared blind spots could go unnoticed. Mitigation: the author verifies every `urgent`/`review` label and every ambiguous case listed in the script.
10. **Very few real positives.** Real data has 4 `urgent` and 10 `review` comments out of 997. Recall on real data is reported as counts ("4/4"), never as a percentage alone.

## Sensitive-data handling

| Risk | Handling |
|---|---|
| Customer name and phone | Dropped at export; never stored in the dataset |
| Employee names | Replaced with stable pseudonyms (`EMP_01`...) per store. Also replaced inside comment **and product** text, tolerating missing accents, a doubled letter written once and b/v swaps. A first name shared by two employees maps to the rated employee, otherwise to `[EMPLEADO]`. First names that are everyday words ("Luz", a product here) only count when written with the rest of the name. Result on the real data: 12 employee-name mentions and 1 non-employee name replaced, 0 false positives, 0 known leaks (`src/review_insights/anonymize.py`, `tests/test_anonymize.py`) |
| Phones / emails typed inside comments | Regex replacement with `[PHONE]` / `[EMAIL]` |
| Customer and other names typed inside comments | Reviewed on 2026-10-27: every comment of 40+ characters read; shorter ones checked for capitalized words, numbers, addresses, plates and social handles; every word appearing at most twice listed and read. Found 2 more: a non-employee first name (R01676) and an employee's nickname (R00417). Both are in the private removal list and become `[NOMBRE]`. Remaining risk: a lowercase name in a short comment that is also a common word |
| Store, tablets | Pseudonyms (`COMPANY_02`, `DEV_08`) |
| Raw export and pseudonym mapping | Kept outside the repo (`data/raw/`, `*PRIVATE*` are git-ignored) |
| LLM | Runs locally (Ollama); by default no review text leaves the computer. If Claude is enabled for comparison, it receives only anonymized text |
| Incidents involving real staff | Shown to evaluators only in anonymized form and only with the owner's permission |

## Synthetic data

The real data has too few negative cases to test the system meaningfully, so 44 synthetic reviews are added in `data/synthetic_cases.csv`, each with its expected labels. They are stored with `synthetic = 1` and every metric is reported separately for real and synthetic data.

**How they were made.** The original plan was to write them by hand, to avoid the same model family writing the test and answering it. To save time they were **drafted by Claude Opus**, modelled on patterns found in the real comments (several mirror a real review without reusing its wording, noted in the `notes` column), and are open to edits by the author. The default classifier is a different model family (Qwen 2.5, local), which limits the risk of the test writer and the test taker sharing blind spots. If Claude is used as the classifier for comparison, that risk returns and is stated next to those results.

| Category | Cases | Mirrors in real data |
|---|---|---|
| Sarcasm | 4 | — |
| Complaint ending in thanks | 3 | R02123 |
| Serious problem inside a 4–5★ rating | 5 | R00309 |
| Safety incident without obvious keywords | 4 | R01972 |
| Gibberish, emoji-only, one word | 6 | many |
| Prompt injection | 4 | — |
| Product name variants and misspellings | 3 | many |
| Price, wait time, mixed | 4 | R00460, R00933 |
| Rating/text mismatch | 2 | — |
| Other employee, staff-written, follow-up request | 3 | R02123, R02412, R01215 |
| Legal threat, leave threat, flirting, recognition, hidden at end, English | 6 | R02888, R01351 |

Labels: 17 `urgent`, 15 `review`, 12 `normal`.

## Demo reviews

`data/demo_negative_cases.csv`: 45 invented complaints (defective helmets, loose tyre after maintenance, rude staff, reflective vests that stop reflecting, a top case that fell off, billing errors, sarcasm, a prompt injection, a child's helmet sold in adult size…), written by Claude to show the prototype with more than the 14 actionable real reviews. Labels: 21 `urgent`, 24 `review`.

- Stored with `synthetic = 3` and attributed to **fictional employees EMP_91–EMP_96**, so no invented complaint lands on a real employee's pseudonym.
- Off by default in the web page (toggle "Incluir reseñas de demostración"), marked 🧪 when shown. Counting questions and headline numbers always use real reviews only.
- Also scored as a fourth column of the classifier evaluation. They were written after the classifier and alert words existed, by the same author, so they are a demo set, not independent evidence.
