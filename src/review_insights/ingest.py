"""Raw DynamoDB scan of the Rating table -> anonymized reviews.

Usage:
    python -m review_insights.ingest data/raw/rating_scan_2026-10-20.json \
        --exclude-company <test company id> --out data/reviews_anon.json \
        --mapping data/raw/mapping_PRIVATE.json

Optional private inputs (git-ignored, they contain real names):
    data/raw/employee_aliases_PRIVATE.json, data/raw/other_names_PRIVATE.json
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from review_insights.anonymize import Scrubber


def unwrap(attr):
    """DynamoDB typed JSON ({"S": "x"}) -> plain Python value."""
    (kind, value), = attr.items()
    if kind == "N":
        return float(value) if "." in value else int(value)
    if kind == "NULL":
        return None
    if kind == "M":
        return {k: unwrap(v) for k, v in value.items()}
    if kind == "L":
        return [unwrap(v) for v in value]
    return value


def _has_text(value):
    return bool(value and str(value).strip())


def _aliases(keys_in_order, prefix):
    aliases = {}
    for key in keys_in_order:
        if key not in aliases:
            aliases[key] = f"{prefix}{len(aliases) + 1:02d}"
    return aliases


def anonymize(items, exclude_companies=(), employee_aliases=None, other_names=()):
    """Returns (reviews, mapping). `items` are plain dicts as stored in DynamoDB.

    `employee_aliases` maps a name to the canonical name of the same person (registered twice).
    `other_names` are non-employees whose names must be removed from free text.
    """
    employee_aliases = employee_aliases or {}

    def employee_key(it):
        name = (it.get("employeeName") or "").strip()
        return it["id"], employee_aliases.get(name, name)

    # IDs are assigned over the full table ordered by rangeId (date first), before excluding
    # anything, so review IDs stay stable and match the ones cited in the docs.
    items = sorted(items, key=lambda it: it["rangeId"])
    review_ids = {id(it): f"R{n + 1:05d}" for n, it in enumerate(items)}

    by_date = sorted(items, key=lambda it: it.get("createdAt") or it["rangeId"])
    companies = _aliases((it["id"] for it in by_date), "COMPANY_")
    devices = _aliases((it.get("deviceId") for it in by_date), "DEV_")
    employees = _aliases((employee_key(it) for it in by_date), "EMP_")

    # every spelling an employee was registered under, so all of them get scrubbed from text
    names_by_company = defaultdict(dict)
    for it in items:
        names_by_company[it["id"]][(it.get("employeeName") or "").strip()] = employees[employee_key(it)]
    scrubbers = {company: Scrubber(names, other_names) for company, names in names_by_company.items()}

    reviews = []
    for it in items:
        if it["id"] in exclude_companies:
            continue
        name = (it.get("employeeName") or "").strip()
        scrubber = scrubbers[it["id"]]
        reviews.append({
            "review_id": review_ids[id(it)],
            "company": companies[it["id"]],
            "employee": employees[employee_key(it)],
            "device": devices[it.get("deviceId")],
            "created_at": it.get("createdAt") or it["rangeId"][:10],
            "rating": it.get("rating"),
            "comment": scrubber.scrub(it.get("comment"), rated_employee=name),
            # customers sometimes type the employee's name in the product field
            "product": scrubber.scrub(it.get("product"), rated_employee=name),
            "rating_time_ms": it.get("ratingTimeMs"),
            "has_rater_name": _has_text(it.get("raterName")),
            "has_rater_phone": _has_text(it.get("raterPhone")),
            "synthetic": 0,
        })

    mapping = {
        "companies": companies,
        "devices": {str(k): v for k, v in devices.items()},
        "employees": {f"{c}::{n}": p for c, names in names_by_company.items() for n, p in names.items()},
        "other_names": list(other_names),
    }
    return reviews, mapping


def _read_private(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else default


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scan", type=Path)
    parser.add_argument("--exclude-company", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, default=Path("data/raw/employee_aliases_PRIVATE.json"),
                        help='JSON {"name as registered": "canonical name"} for people registered twice')
    parser.add_argument("--other-names", type=Path, default=Path("data/raw/other_names_PRIVATE.json"),
                        help="JSON list of non-employee names to remove from text")
    args = parser.parse_args()

    raw = json.loads(args.scan.read_text(encoding="utf-8"))
    items = [{k: unwrap(v) for k, v in it.items()} for it in raw["Items"]]
    reviews, mapping = anonymize(items, set(args.exclude_company),
                                 _read_private(args.aliases, {}), _read_private(args.other_names, []))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reviews, ensure_ascii=False, indent=1), encoding="utf-8")
    args.mapping.write_text(json.dumps(mapping, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(reviews)} reviews written to {args.out} "
          f"({len(items) - len(reviews)} excluded)")


if __name__ == "__main__":
    main()
