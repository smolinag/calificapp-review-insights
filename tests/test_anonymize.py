from review_insights.anonymize import GENERIC_EMPLOYEE, Scrubber
from review_insights.ingest import anonymize

# Fictional names that reproduce the cases found in the real data
EMPLOYEES = {
    "Mónica": "EMP_01",
    "Mónica Ríos": "EMP_02",
    "Luz Marina Ortiz": "EMP_03",
    "Sara": "EMP_04",
}


def scrub(text, rated=None):
    return Scrubber(EMPLOYEES).scrub(text, rated_employee=rated)


def test_name_without_accent_maps_to_rated_employee():
    assert scrub("Mil gracias Monica, excelente", rated="Mónica") == "Mil gracias EMP_01, excelente"


def test_common_misspellings_of_a_name_are_replaced():
    employees = {"Rebecca": "EMP_09"}
    for written in ("Rebeca", "rebecca"):
        assert Scrubber(employees).scrub(f"Atención de {written}") == "Atención de EMP_09"
    assert Scrubber({"Viviana": "EMP_10"}).scrub("Gracias Biviana") == "Gracias EMP_10"


def test_shared_first_name_of_another_employee_becomes_generic():
    assert scrub("Mónica fue muy amable", rated="Sara") == f"{GENERIC_EMPLOYEE} fue muy amable"


def test_unique_name_of_another_employee_keeps_its_pseudonym():
    assert scrub("La atención de Sara fue excelente", rated="Mónica") == "La atención de EMP_04 fue excelente"


def test_full_name_wins_over_first_name():
    assert scrub("Gracias Mónica Ríos", rated="Sara") == "Gracias EMP_02"


def test_common_word_alone_is_not_a_name():
    assert scrub("Compré una luz led", rated="Sara") == "Compré una luz led"
    assert scrub("Luz led", rated="Luz Marina Ortiz") == "Luz led"


def test_common_word_with_rest_of_name_is_replaced():
    assert scrub("Luz Marina me atendió", rated="Sara") == "EMP_03 me atendió"


def test_name_inside_other_word_is_untouched():
    assert scrub("Sarita y Saraaa", rated="Mónica") == "Sarita y Saraaa"


def test_phone_and_email_replaced_but_prices_kept():
    text = "Llamar al 300 123 4567 o a ana@mail.com, pagué $1.500.000"
    assert scrub(text) == "Llamar al [PHONE] o a [EMAIL], pagué $1.500.000"


def test_short_numbers_kept():
    assert scrub("10/10, volveré en 2024") == "10/10, volveré en 2024"


def _item(company, range_id, name, comment="", **extra):
    return {"id": company, "rangeId": range_id, "createdAt": range_id[:10], "employeeName": name,
            "deviceId": "dev-1", "rating": 5, "comment": comment, **extra}


def test_ingest_drops_customer_data_and_excludes_company():
    items = [
        _item("Test", "2025-01-01-dev-1", "X"),
        _item("Store", "2025-01-02-dev-1", "Sara", "Gracias Sara",
              raterName="Juan Pérez", raterPhone="3001234567"),
    ]
    reviews, mapping = anonymize(items, exclude_companies={"Test"})

    assert len(reviews) == 1
    review = reviews[0]
    assert review["review_id"] == "R00002"  # stable: counted before exclusion
    assert review["comment"] == f"Gracias {review['employee']}"
    assert review["has_rater_name"] and review["has_rater_phone"]
    serialized = str(review)
    assert "Juan" not in serialized and "3001234567" not in serialized and "Sara" not in serialized
    assert mapping["employees"]["Store::Sara"] == review["employee"]


def test_ingest_merges_employee_registered_twice():
    items = [
        _item("Store", "2025-01-01-dev-1", "Mónica", "Gracias Mónica"),
        _item("Store", "2025-01-02-dev-1", "Mónica Ríos", "Gracias Mónica Ríos"),
        _item("Store", "2025-01-03-dev-1", "Sara", "Mónica también ayudó"),
    ]
    reviews, _ = anonymize(items, employee_aliases={"Mónica": "Mónica Ríos"})
    first, second, third = reviews
    assert first["employee"] == second["employee"] != third["employee"]
    assert first["comment"] == second["comment"] == f"Gracias {first['employee']}"
    # the shared first name is no longer ambiguous once both records are one person
    assert third["comment"] == f"{first['employee']} también ayudó"


def test_other_names_are_removed():
    reviews, _ = anonymize([_item("Store", "2025-01-01-dev-1", "Sara", "Paula me ayudó")],
                           other_names=["Paula"])
    assert reviews[0]["comment"] == "[NOMBRE] me ayudó"


def test_ingest_scrubs_names_typed_in_product_field():
    reviews, _ = anonymize([_item("Store", "2025-01-02-dev-1", "Tomás", product="Tomas ")])
    assert reviews[0]["product"].strip() == reviews[0]["employee"]
