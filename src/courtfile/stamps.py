"""Parse the CM/ECF header stamp that federal courts print on every filed page.

Four stamp families occur in the wild; each is matched by its own pattern so that a mismatch is
reported rather than guessed:

* ``district``    Case 1:21-cv-01061-KLM Document 1 Filed 04/16/21 USDC Colorado Page 1 of 16
* ``bankruptcy``  Case 09-00429 Doc 83 Filed 03/09/10 Entered 03/09/10 09:03:58 Document Page 1 of 4
* ``appellate``   Case: 20-1507 Document: 00117684624 Page: 1 Date Filed: 12/22/2020 Entry ID: 6390389
                  (and the Second, Fourth, Seventh and Ninth Circuit variants)
* ``caption``     no stamp: case number read from the caption ("No. 24-2042", "Case No. 8:16-cv-1261")
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, asdict

DATE = r"(?P<date>\d{1,2}/\d{1,2}/(?:\d{4}|\d{2}))"
DISTRICT_CASE = r"(?P<case>\d{1,2}:\d{2}-[a-z]{2}-\d{3,6}(?:-[A-Za-z0-9]+)*)"
SHORT_CASE = r"(?P<case>\d{2}-\d{1,6})"
DOC = r"(?P<doc>\d+(?:-\d+)?)"

PATTERNS = [
    ("district", re.compile(
        rf"Case:?\s+{DISTRICT_CASE}\s*Document\s*#?:?\s*{DOC}\s+Filed:?\s*{DATE}"
        rf"(?:\s+USDC\s+[A-Za-z ]+?)?\s+Page\s*(?P<page>\d+)\s*of\s*(?P<total>\d+)")),
    ("bankruptcy", re.compile(
        rf"Case\s+{SHORT_CASE}\s+Doc\s+{DOC}\s+Filed\s+{DATE}\s+Entered\s+\S+\s+\S+\s+"
        rf"(?:Document\s+)?(?:Desc\s+)?Page\s+(?P<page>\d+)\s*of\s*(?P<total>\d+)")),
    ("bankruptcy", re.compile(  # page counter split across the line: "... Desc Page 1 of 3"
        rf"Case\s+{SHORT_CASE}\s+Doc\s+{DOC}\s+Filed\s+{DATE}\s+Entered\s+\S+\s+\S+\s+Desc\s+Page\s+(?P<page>\d+)\s+of\s+(?P<total>\d+)")),
    ("appellate", re.compile(  # 1st, 3rd, 5th, 6th, 10th, Fed. Cir.
        rf"(?:Appellate\s+)?Case:\s+{SHORT_CASE}\s+Document:\s+(?P<doc>[\w-]+)\s+(?:Page:\s+(?P<page>\d+)\s+)?"
        rf"(?:Date\s+)?Filed:\s+{DATE}(?:\s+Pages?:\s+(?P<page2>\d+))?")),
    ("appellate", re.compile(  # 2nd Circuit
        rf"Case\s+{SHORT_CASE},\s+Document\s+(?P<doc>[\w-]+),\s+{DATE},\s+\d+,\s+Page\s*(?P<page>\d+)\s+of\s+(?P<total>\d+)")),
    ("appellate", re.compile(  # 4th Circuit
        rf"Appeal:\s+{SHORT_CASE}\s+Doc:\s+(?P<doc>[\w-]+)\s+Filed:\s+{DATE}\s+Pg:\s+(?P<page>\d+)\s+of\s+(?P<total>\d+)")),
    ("appellate", re.compile(  # 9th Circuit
        rf"Case:\s+{SHORT_CASE},\s+{DATE},\s+ID:\s+\d+,\s+DktEntry:\s+(?P<doc>[\w-]+),\s+Page\s+(?P<page>\d+)\s+of\s+(?P<total>\d+)")),
]
CAPTION_PATTERNS = [
    re.compile(r"\b(?:Civil\s+Action\s+|Case\s+)?No\.?:?\s*(?P<case>\d{1,2}:\d{2}-[a-z]{2}-\d{3,6}(?:-[A-Za-z0-9]+)*)"),
    re.compile(r"\bMDL\s+(?P<case>\d{2}-\d{4,6}(?:-[A-Z0-9]+)*)"),
    re.compile(r"\bCase\s+No\.?\s*(?P<case>[A-Z]{2}\d{2}-\d{4,6}(?:-[A-Z]+(?:\([A-Za-z]+\))?)*)"),
    re.compile(r"\bNo\.\s+(?P<case>\d{2}-\d{3,6})\b"),
]


@dataclass
class Stamp:
    family: str                 # district | bankruptcy | appellate | caption
    case_number: str
    doc_number: str | None
    filed: str | None           # ISO date
    page: int | None
    total_pages: int | None

    def as_dict(self) -> dict:
        return asdict(self)


def iso_date(raw: str | None) -> str | None:
    if not raw:
        return None
    m, d, y = raw.split("/")
    year = int(y)
    if year < 100:
        year += 2000 if year <= 50 else 1900
    try:
        return dt.date(year, int(m), int(d)).isoformat()
    except ValueError:
        return None


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def parse_stamp(text: str) -> Stamp | None:
    """Parse the first stamp found in ``text`` (one page of extracted text), else fall back to the caption."""
    flat = _flat(text[:6000])
    for family, rx in PATTERNS:
        m = rx.search(flat)
        if not m:
            continue
        g = m.groupdict()
        page = g.get("page") or g.get("page2")
        return Stamp(family, g["case"], g.get("doc"), iso_date(g.get("date")),
                     int(page) if page else None, int(g["total"]) if g.get("total") else None)
    # The stamp is present but its fields are overprinted or reordered: report what is certain.
    m = re.search(r"Case:?\s+(\d{1,2}:\d{2}-[a-z]{2}-\d{3,6}(?:-[A-Z]{2,4}(?![a-z]))*)", flat)
    if m:
        pg = re.search(r"Page\s+(\d+)\s+of\s+(\d+)\b(?!\s*of)", flat[m.start():m.start() + 400])
        return Stamp("district", m.group(1), None, None,
                     int(pg.group(1)) if pg else None, int(pg.group(2)) if pg else None)
    for rx in CAPTION_PATTERNS:
        m = rx.search(flat)
        if m:
            return Stamp("caption", m.group("case"), None, None, None, None)
    return None
