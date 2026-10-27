"""Fails if any real employee, store or other private name appears in files that can be committed.

Usage: python scripts/check_no_real_names.py [--mapping data/raw/mapping_PRIVATE.json]
Uses the anonymizer's own matcher, so misspellings ("Rebeca" for "Rebecca") are caught too.
Prints file, line and the pseudonym of the matched name, never the name itself.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from review_insights.anonymize import Scrubber, normalize

PLACEHOLDER = re.compile(r"EMP_\d+|\[EMPLEADO\]|\[NOMBRE\]")


def committable_files():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, text=True, check=True).stdout
    return [Path(p) for p in out.splitlines()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, default=Path("data/raw/mapping_PRIVATE.json"))
    args = parser.parse_args()
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))

    names = {key.split("::", 1)[1]: pseudo for key, pseudo in mapping["employees"].items()}
    scrubber = Scrubber(names, mapping.get("other_names", []))
    # long, distinctive words identify the store; short generic ones ("moto") don't
    store_words = {normalize(t) for company in mapping["companies"] for t in company.split() if len(t) >= 6}

    findings = []
    for path in committable_files():
        if path.suffix in {".pdf", ".png", ".db"} or not path.is_file():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            # names only: the phone rule would flag every ISO date
            if scrubber.pattern.search(line):
                hits = set(PLACEHOLDER.findall(scrubber.scrub(line))) - set(PLACEHOLDER.findall(line))
                findings.append(f"{path}:{n}: real name of {', '.join(sorted(hits)) or 'a person'}")
            if any(re.search(rf"\b{re.escape(w)}\b", normalize(line)) for w in store_words):
                findings.append(f"{path}:{n}: real store name")

    print("\n".join(findings) or "OK: no real names found")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
