"""Rule-based document-type classification for federal court filings.

The rules read the *title zone* (short, mostly upper-case lines near the top of page 1, with the ECF
stamp and pleading-paper line numbers removed) first, and the opening sentences second. Interior pages
of a longer filing carry no title, so they are labelled ``Excerpt`` rather than guessed.
"""
from __future__ import annotations

import re

LINE_NO = re.compile(r"^\s*\d{1,2}\s+(?=\S)|\s+\d{1,2}\s*$")
STAMP = re.compile(r"^\s*(?:Appellate\s+)?(?:Case|Appeal)\b.*$|^\s*Page\s+ID\b.*$|^\s*#:\d+\s*$", re.M)

# (label, regex applied to the upper-cased title zone) in priority order.
TITLE_RULES = [
    ("Order", r"^\s*(?:\[?PROPOSED\]?\s+)?(?:[A-Z]+ )?ORDER\b|\bSUGGESTION OF REMAND\b"),
    ("Complaint", r"\b(?:FIRST |SECOND |THIRD )?(?:AMENDED )?(?:CLASS ACTION )?COMPLAINT\b"),
    ("Declaration", r"\bDECLARATION\b"),
    ("Form", r"\bAPPEARANCE\b.*\bFORM\b|\bENTRY OF APPEARANCE\b"),
    ("Motion", r"\bMOTION\b|\bAPPLICATION (?:FOR|TO)\b"),
    ("Minutes", r"\bCIVIL MINUTES\b|\bMINUTE ORDER\b"),
    ("Brief / memorandum", r"\bMEMORANDUM\b|\bBRIEF\b"),
    ("Notice", r"\bNOTICE OF\b"),
    ("Exhibit", r"\bEXHIBIT\s+[A-Z0-9]+\b"),
    ("Opinion", r"\bOPINION\b"),
]
BODY_RULES = [
    ("Opinion", r"\bBEFORE\b[^.]{0,200}\bCIRCUIT JUDGES?\b"),
    ("Order", r"\bIT IS (?:SO )?ORDERED\b|\bTHE COURT (?:HEREBY )?(?:ORDERS|GRANTS|DENIES)\b|\bTHIS COURT HAS BEEN ADVISED\b|\bBY THE COURT\b"),
    ("Letter", r"\bDEAR\b[^,]{0,60},|\bVIA ECF\b"),
    ("Form", r"\bENTRY OF APPEARANCE\b"),
    ("Petition / bankruptcy form", r"FILL IN THIS INFORMATION TO IDENTIFY"),
    ("Notice", r"\bINQUIRIES REGARDING THIS CASE\b|\bDOCKET #"),
    ("Order", r"\bORDER\b"),
]


def title_zone(page1: str, max_lines: int = 45) -> list[str]:
    """Short, mostly-upper-case lines near the top of page 1, with stamp and line numbers stripped."""
    cleaned = STAMP.sub("", page1)
    lines = []
    for raw in cleaned.splitlines()[:max_lines * 2]:
        line = LINE_NO.sub("", raw).strip()
        line = re.sub(r"\s{2,}", " ", line)
        if 3 <= len(line) <= 110:
            letters = [c for c in line if c.isalpha()]
            if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
                lines.append(line)
    return lines[:max_lines]


def classify(page1: str, stamp_page: int | None) -> tuple[str, str]:
    """Return (label, evidence) for the first page of a document."""
    if stamp_page and stamp_page > 1:
        return "Excerpt", f"interior page {stamp_page} carries no title"
    zone = [ln for ln in title_zone(page1)
            if not re.search(r"UNITED STATES|DISTRICT OF|COURT OF APPEALS|BANKRUPTCY COURT|^CASE\b|^FILED$|CIRCUIT$", ln.upper())]
    zone_text = "\n".join(zone).upper()
    for label, pattern in TITLE_RULES:
        m = re.search(pattern, zone_text, re.M)
        if m:
            return label, f"title: {m.group(0).strip()}"
    body = re.sub(r"\s+", " ", STAMP.sub("", page1)).upper()
    for label, pattern in BODY_RULES:
        m = re.search(pattern, body)
        if m:
            return label, f"body: {m.group(0)[:40].strip()}"
    return "Unclassified", "no title or body rule matched"
