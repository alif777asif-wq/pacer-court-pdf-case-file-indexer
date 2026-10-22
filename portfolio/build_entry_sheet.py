"""Write portfolio/portfolio-entry-sheet.md: paste-ready Upwork portfolio fields with computed character counts.

Figures come from the results files; limits are those on Upwork's help page "How to enhance your freelancer
profile" (title 70, role 100, description 600, five skill tags; images 400 x 300 minimum, 4000 x 4000 maximum).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
res = json.loads((ROOT / "proof/outputs/results.json").read_text())
tests = json.loads((ROOT / "proof/test-summary.json").read_text())
REPO = "pacer-court-pdf-case-file-indexer"
URL = f"https://github.com/alif777asif-wq/{REPO}"
V = res["verification"]
ce, fv, rl = V["cross_extractor"], V["filename_vs_text"], V["reference_labels"]
c = res["corpus"]

TITLE = "PACER Court PDF Indexer: Python Toolkit with Excel Case Index"
ROLE = "Sole developer: built, tested, verified and documented the toolkit"
DESC = (f"Original, independent project, no client. A Python toolkit that reads federal court PDFs, parses the court's header stamp, "
        f"names the court, case and document number, classifies the document, OCRs scanned pages, files each PDF by court and case, "
        f"and writes an Excel/CSV index with an exceptions sheet. Measured on {c['documents']} real public filings ({c['pages']} pages): "
        f"{ce['case_number_agree']}/{ce['documents_compared']} case numbers agree across two PDF readers, {fv['agree']}/{fv['fields_compared']} stamp fields "
        f"match file names, {tests['passed']}/{tests['tests']} tests pass, {res['run_seconds']} s end to end; "
        f"{res['review']['needs_review']} files flagged for review. No generated data.")
SKILLS = ["Python", "Data Extraction", "PDF Conversion", "Microsoft Excel", "Legal Research"]
assert len(TITLE) <= 70 and len(ROLE) <= 100 and len(DESC) <= 600 and len(SKILLS) <= 5, (len(TITLE), len(ROLE), len(DESC))

GALLERY = [
    ("1-federal-court-pdf-indexer-python-outcome", "Outcome", "the one headline result: case numbers read identically by two independent PDF readers"),
    ("2-court-pdf-organiser-before-after", "Task", "the real input file names beside the court/case folders the toolkit built from them"),
    ("3-court-pdf-automation-pipeline-timing", "Approach", "the five stages on a shared time axis with measured seconds"),
    ("4-court-document-classification-results", "Data", "document types found and the written reasons files were flagged for review"),
    ("5-court-pdf-indexer-verified-tests", "Proof", "independent checks, a planted-error test and the tests that passed"),
]
PUSH = f"""cd ~/Downloads && unzip -o {REPO}.zip && cd {REPO}
git init -b main && git add . && git commit -m "Add PACER court PDF case-file indexer with tests, proof run and portfolio images"
gh repo create {REPO} --public --source=. --remote=origin --push"""

md = f"""# Upwork portfolio entry sheet

Paste each field into the portfolio form. Character counts are computed; limits are from Upwork's help page "How to enhance your freelancer profile" (title 70, role 100, description 600, five skill tags).

## Project title ({len(TITLE)} / 70 characters)

{TITLE}

## Your role ({len(ROLE)} / 100 characters)

{ROLE}

## Project description ({len(DESC)} / 600 characters)

{DESC}

## Skills and deliverables ({len(SKILLS)} / 5 tags)

{chr(10).join('- ' + s for s in SKILLS)}

The form accepts only skills from Upwork's own list; if a name differs, choose the closest match.

## Project link

{URL}

This link works only after you have run the push command below; until then the repository does not exist.

## Gallery order (upload the PNG masters from `portfolio/export/`; every file is 4000 x 3000 px and under 5 MB)

| Slot | File name | Message | Shows |
|---|---|---|---|
""" + "\n".join(f"| {i} | `{n}.png` | {m} | {d} |" for i, (n, m, d) in enumerate(GALLERY, 1)) + f"""

JPG versions of every image are in the same folder. Slot 1 is the cover: its headline and focal figure sit inside the central 960 x 720 region, so a narrower centered crop does not clip them.

## Push command (Linux terminal)

```bash
{PUSH}
```

Set up once if missing: `gh auth login`, and `git config --global user.name` and `git config --global user.email`.
"""
(ROOT / "portfolio/portfolio-entry-sheet.md").write_text(md, encoding="utf-8")
print("title", len(TITLE), "role", len(ROLE), "description", len(DESC), "skills", len(SKILLS))
