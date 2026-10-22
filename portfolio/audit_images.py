"""Audit the five image files against the brief's rules and write portfolio/audit-report.json.

Checks: no JavaScript or external resources, repository URL only in the leading HTML comment, no URLs / emails /
phone numbers in the visible text, and every number in the visible text appears in the machine-written results.
"""
import json
import pathlib
import re

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/alif777asif-wq/pacer-court-pdf-case-file-indexer"
SOURCES = [ROOT / "proof/outputs/results.json", ROOT / "proof/outputs/records.json",
           ROOT / "proof/test-summary.json", ROOT / "proof/env.json"]
source_numbers = set(re.findall(r"\d+(?:\.\d+)?", " ".join(p.read_text() for p in SOURCES)))
source_numbers |= {n.lstrip("0") or "0" for n in list(source_numbers)}
URLISH = re.compile(r"https?://|www\.|\.(?:com|org|net|io|dev)\b|github", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(?:\(\d{3}\)\s?|\d{3}[-.\s])\d{3}[-.\s]\d{4}(?!\d)")

report = {}
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 960})
    for html in sorted((ROOT / "portfolio/html").glob("*.html")):
        raw = html.read_text(encoding="utf-8")
        head_comment = raw.split("\n", 1)[0]
        body_without_comment = raw.split("\n", 1)[1]
        page.goto(html.as_uri())
        text = page.inner_text("body")
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        untraced = sorted({n for n in numbers if n not in source_numbers and n.lstrip("0") not in source_numbers}
                          - {"01", "02", "03", "04", "05", "05"})
        report[html.stem] = {
            "starts_with_repo_url_comment": head_comment.startswith("<!-- Source repository: " + REPO_URL),
            "repo_url_only_in_comment": REPO_URL not in body_without_comment,
            "script_tags": len(re.findall(r"<script", raw, re.I)),
            "external_resources": len(re.findall(r"""(?:src|href)=["']?https?:|url\(["']?https?:|@import|<img|<link""", raw, re.I)),
            "url_like_text_in_artwork": URLISH.findall(text),
            "emails": EMAIL.findall(text), "phones": PHONE.findall(text),
            "numbers_not_found_in_results": untraced,
            "visible_characters": len(text),
        }
    browser.close()
(ROOT / "portfolio/audit-report.json").write_text(json.dumps(report, indent=2) + "\n")
for k, v in report.items():
    print(k, {a: b for a, b in v.items() if a != "visible_characters"})
