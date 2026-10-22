"""Identify the issuing federal court from document text.

Court ids follow the public CourtListener convention (for example ``cacd``, ``azd``, ``ca1``) so that
results can be joined to other legal-data tools. District ids are the USPS state code plus a direction
letter (``n s e w c m``) or ``d`` for an undivided district; bankruptcy ids end in ``b``.
"""
from __future__ import annotations

import re

STATES = {
    "ALABAMA": "al", "ALASKA": "ak", "ARIZONA": "az", "ARKANSAS": "ar", "CALIFORNIA": "ca",
    "COLORADO": "co", "CONNECTICUT": "ct", "DELAWARE": "de", "FLORIDA": "fl", "GEORGIA": "ga",
    "HAWAII": "hi", "IDAHO": "id", "ILLINOIS": "il", "INDIANA": "in", "IOWA": "ia", "KANSAS": "ks",
    "KENTUCKY": "ky", "LOUISIANA": "la", "MAINE": "me", "MARYLAND": "md", "MASSACHUSETTS": "ma",
    "MICHIGAN": "mi", "MINNESOTA": "mn", "MISSISSIPPI": "ms", "MISSOURI": "mo", "MONTANA": "mt",
    "NEBRASKA": "ne", "NEVADA": "nv", "NEW HAMPSHIRE": "nh", "NEW JERSEY": "nj", "NEW MEXICO": "nm",
    "NEW YORK": "ny", "NORTH CAROLINA": "nc", "NORTH DAKOTA": "nd", "OHIO": "oh", "OKLAHOMA": "ok",
    "OREGON": "or", "PENNSYLVANIA": "pa", "RHODE ISLAND": "ri", "SOUTH CAROLINA": "sc",
    "SOUTH DAKOTA": "sd", "TENNESSEE": "tn", "TEXAS": "tx", "UTAH": "ut", "VERMONT": "vt",
    "VIRGINIA": "va", "WASHINGTON": "wa", "WEST VIRGINIA": "wv", "WISCONSIN": "wi", "WYOMING": "wy",
    "PUERTO RICO": "prd", "COLUMBIA": "dc",
}
DIRECTIONS = {"NORTHERN": "n", "SOUTHERN": "s", "EASTERN": "e", "WESTERN": "w", "CENTRAL": "c", "MIDDLE": "m"}
CIRCUITS = {
    "FIRST": "ca1", "SECOND": "ca2", "THIRD": "ca3", "FOURTH": "ca4", "FIFTH": "ca5", "SIXTH": "ca6",
    "SEVENTH": "ca7", "EIGHTH": "ca8", "NINTH": "ca9", "TENTH": "ca10", "ELEVENTH": "ca11",
    "FEDERAL": "cafc", "D.C.": "cadc",
}

_STATE_ALT = "|".join(sorted((re.escape(s) for s in STATES), key=len, reverse=True))
_DISTRICT_RE = re.compile(
    rf"(?:\b(NORTHERN|SOUTHERN|EASTERN|WESTERN|CENTRAL|MIDDLE)\s+)?DISTRICT\s+OF\s+(?:THE\s+)?({_STATE_ALT})\b")
_USDC_RE = re.compile(rf"\bUSDC\s+({_STATE_ALT})\b", re.I)
_CIRCUIT_RE = re.compile(r"\bFOR\s+THE\s+(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|FEDERAL)\s+CIRCUIT\b|"
                         r"\b(FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH)\s+CIRCUIT\b", re.I)


def identify_court(text: str, level: str | None = None) -> str | None:
    """Return a court id, or None when the text does not name the court.

    ``level`` may be 'appellate', 'district' or 'bankruptcy' (from the stamp family); it only
    disambiguates, the court name in the text always wins.
    """
    head = re.sub(r"\s+", " ", text[:4000]).upper()
    head = re.sub(r"(?<=\s)\d{1,2}(?=\s+(?:FOR|DISTRICT|CENTRAL|NORTHERN|SOUTHERN|EASTERN|WESTERN|MIDDLE)\b)", "", head)
    if level in (None, "appellate"):
        m = _CIRCUIT_RE.search(head)
        if m and ("COURT OF APPEALS" in head or "CIRCUIT" in head):
            return CIRCUITS[(m.group(1) or m.group(2)).upper()]
    bankruptcy = "BANKRUPTCY COURT" in head or level == "bankruptcy"
    m = _DISTRICT_RE.search(head)
    if m:
        state = STATES[m.group(2)]
        direction = DIRECTIONS.get(m.group(1) or "", "")
        if bankruptcy:
            return f"{state}{direction}b"
        return f"{state}{direction}d" if len(state) == 2 else state
    m = _USDC_RE.search(head)
    if m:
        return f"{STATES[m.group(1).upper()]}d"
    return None
