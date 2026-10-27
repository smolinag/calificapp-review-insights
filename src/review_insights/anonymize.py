"""Pseudonymization and PII scrubbing for Calificapp ratings."""
import re
import unicodedata

# First names that are also everyday Spanish words ("luz" is a product here: motorcycle lights).
# They are only treated as a name when written together with the rest of the name.
COMMON_WORDS = {
    "luz", "paz", "rosa", "angel", "sol", "mar", "pilar", "cruz", "leon",
    "consuelo", "dolores", "amparo", "esperanza", "rocio", "socorro",
}
GENERIC_EMPLOYEE = "[EMPLEADO]"
OTHER_PERSON = "[NOMBRE]"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
# Digits, spaces, dashes and parentheses only: prices like "$1.500.000" use dots and must survive.
PHONE_CANDIDATE = re.compile(r"\+?\d[\d\s\-()]{5,}\d")

_ACCENTS = {"a": "aáàä", "e": "eéèë", "i": "iíìï", "o": "oóòö", "u": "uúùü", "n": "nñ"}


def normalize(text):
    """Casefold and strip accents, for comparing names."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def _accent_insensitive(phrase):
    """Regex matching the phrase with or without accents, and with the misspellings
    customers make most: a doubled letter written once ("Rebeca" for "Rebecca") and b/v swapped."""
    parts = []
    for run in re.finditer(r"(.)\1*", normalize(phrase)):
        ch, count = run.group(1), len(run.group())
        if ch.isspace():
            parts.append(r"\s+")
            continue
        if ch in "bv":
            cls = "[bv]"
        elif ch in _ACCENTS:
            cls = f"[{_ACCENTS[ch]}]"
        else:
            cls = re.escape(ch)
        parts.append(cls if count == 1 else f"{cls}{{1,{count}}}")
    return "".join(parts)


def _scrub_phones(text):
    def replace(match):
        digits = sum(c.isdigit() for c in match.group())
        return "[PHONE]" if digits >= 7 else match.group()
    return PHONE_CANDIDATE.sub(replace, text)


class Scrubber:
    """Replaces employee names inside free text with their pseudonyms.

    `employees` maps each name an employee appears under to its pseudonym (one store);
    several names can share a pseudonym when they are the same person.
    `other_names` are people who are not registered employees; they become [NOMBRE].
    """

    def __init__(self, employees, other_names=()):
        self.pseudonyms = {normalize(n): p for n, p in employees.items()}
        # phrase (normalized) -> set of pseudonyms it can refer to
        owners = {}
        for name, pseudo in [*employees.items(), *((n, OTHER_PERSON) for n in other_names)]:
            tokens = name.split()
            phrases = {" ".join(tokens[:i]) for i in range(1, len(tokens) + 1)}
            phrases |= {t for t in tokens}
            for phrase in phrases:
                key = normalize(phrase)
                if len(key) < 3 or (" " not in key and key in COMMON_WORDS):
                    continue
                owners.setdefault(key, set()).add(pseudo)
        # one group per phrase: matches can be misspelled, so the group tells which phrase matched
        self.phrases = sorted(owners, key=len, reverse=True)
        self.owners = owners
        self.pattern = re.compile(
            r"\b(?:" + "|".join(f"({_accent_insensitive(p)})" for p in self.phrases) + r")\b",
            re.IGNORECASE,
        ) if self.phrases else None

    def scrub(self, text, rated_employee=None):
        if not text:
            return text
        text = EMAIL.sub("[EMAIL]", text)
        text = _scrub_phones(text)
        if self.pattern is None:
            return text
        rated = self.pseudonyms.get(normalize(rated_employee)) if rated_employee else None

        def replace(match):
            candidates = self.owners[self.phrases[match.lastindex - 1]]
            if rated in candidates:
                return rated
            if len(candidates) == 1:
                return next(iter(candidates))
            return GENERIC_EMPLOYEE

        text = self.pattern.sub(replace, text)
        # a full name matches as one phrase, but first name + surname written apart can repeat
        return re.sub(r"(EMP_\d+|\[EMPLEADO\]|\[NOMBRE\])(\s+\1)+", r"\1", text)
