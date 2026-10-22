# Upwork portfolio entry sheet

Paste each field into the portfolio form. Character counts are computed; limits are from Upwork's help page "How to enhance your freelancer profile" (title 70, role 100, description 600, five skill tags).

## Project title (61 / 70 characters)

PACER Court PDF Indexer: Python Toolkit with Excel Case Index

## Your role (66 / 100 characters)

Sole developer: built, tested, verified and documented the toolkit

## Project description (518 / 600 characters)

Original, independent project, no client. A Python toolkit that reads federal court PDFs, parses the court's header stamp, names the court, case and document number, classifies the document, OCRs scanned pages, files each PDF by court and case, and writes an Excel/CSV index with an exceptions sheet. Measured on 13 real public filings (38 pages): 13/13 case numbers agree across two PDF readers, 11/11 stamp fields match file names, 44/44 tests pass, 3.004 s end to end; 7 files flagged for review. No generated data.

## Skills and deliverables (5 / 5 tags)

- Python
- Data Extraction
- PDF Conversion
- Microsoft Excel
- Legal Research

The form accepts only skills from Upwork's own list; if a name differs, choose the closest match.

## Project link

https://github.com/alif777asif-wq/pacer-court-pdf-case-file-indexer

This link works only after you have run the push command below; until then the repository does not exist.

## Gallery order (upload the PNG masters from `portfolio/export/`; every file is 4000 x 3000 px and under 5 MB)

| Slot | File name | Message | Shows |
|---|---|---|---|
| 1 | `1-federal-court-pdf-indexer-python-outcome.png` | Outcome | the one headline result: case numbers read identically by two independent PDF readers |
| 2 | `2-court-pdf-organiser-before-after.png` | Task | the real input file names beside the court/case folders the toolkit built from them |
| 3 | `3-court-pdf-automation-pipeline-timing.png` | Approach | the five stages on a shared time axis with measured seconds |
| 4 | `4-court-document-classification-results.png` | Data | document types found and the written reasons files were flagged for review |
| 5 | `5-court-pdf-indexer-verified-tests.png` | Proof | independent checks, a planted-error test and the tests that passed |

JPG versions of every image are in the same folder. Slot 1 is the cover: its headline and focal figure sit inside the central 960 x 720 region, so a narrower centered crop does not clip them.

## Push command (Linux terminal)

```bash
cd ~/Downloads && unzip -o pacer-court-pdf-case-file-indexer.zip && cd pacer-court-pdf-case-file-indexer
git init -b main && git add . && git commit -m "Add PACER court PDF case-file indexer with tests, proof run and portfolio images"
gh repo create pacer-court-pdf-case-file-indexer --public --source=. --remote=origin --push
```

Set up once if missing: `gh auth login`, and `git config --global user.name` and `git config --global user.email`.
