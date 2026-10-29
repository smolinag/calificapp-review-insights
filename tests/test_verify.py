"""Citation check (C8): every ID an answer cites must be one of the reviews the model was given."""
from review_insights.answer import verify


def test_valid_citations_pass():
    cited, invalid = verify("Un cliente se cayó [R01972]. Otro reclamó la garantía [R02021].", {"R01972", "R02021", "R00001"})
    assert cited == ["R01972", "R02021"]
    assert invalid == []


def test_citation_not_retrieved_is_invalid():
    _, invalid = verify("Hubo un accidente [R01972] y otro [R09999].", {"R01972"})
    assert invalid == ["R09999"]


def test_mangled_id_is_caught():
    # the model once rewrote demo ID D0018 as R0018 to match the format in its instructions
    _, invalid = verify("Se le cayó el baúl [R0018].", {"D0018"})
    assert invalid == ["R0018"]


def test_no_citations():
    assert verify("No encontré reseñas sobre eso.", {"R01972"}) == ([], [])
