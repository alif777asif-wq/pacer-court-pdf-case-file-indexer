# PACER court PDF case-file indexer

A Python toolkit that turns a folder of federal court PDFs into an identified, classified, organised and indexed case file. It was built and tested as an original, independent project; there is no client behind it.

Repository: https://github.com/alif777asif-wq/pacer-court-pdf-case-file-indexer

## The problem

Court filings reach legal-support teams, researchers and analysts as loose PDFs with names such as `gov.uscourts.cacd.652774.40.0.pdf` or `ca10_010110462922.pdf`. Before anyone can use them, someone has to open each file and find out which court and case it belongs to, which document number it is, when it was filed, what kind of document it is, whether it is the whole filing or one page of it, and file it somewhere findable. Done by hand this is slow and error-prone, and a wrong case number silently misfiles a document.

## What the toolkit does

1. **Reads** every PDF: text layer through poppler, Tesseract OCR for pages that have no usable text layer.
2. **Identifies** the filing from the CM/ECF header stamp that courts print on each page (district, bankruptcy and the circuit-specific appellate variants), falling back to the caption when there is no stamp. Overprinted or unreadable stamps are *not guessed*: the field is left empty and the file is flagged.
3. **Names the court** from the page text using CourtListener-style ids (for example `cacd`, `azd`, `ca1`), and uses RECAP-style file names only as a labelled fallback.
4. **Classifies** the document type with transparent rules (order, opinion, complaint, minutes, notice, excerpt, and so on); anything unrecognised is labelled `Unclassified` and flagged.
5. **Files** each PDF under `court/case/` with a portable, collision-free name, and verifies every copy byte-for-byte by SHA-256.
6. **Reports** to CSV and Excel: a case index, a per-case roll-up, an exceptions sheet with a written reason per flagged file, and a run summary.
7. **Verifies itself** with independent checks and a planted-error self-test (see below).

## Measured results

| Measure | Result (one measured run) |
|---|---|
| Documents / pages processed | 13 PDFs / 38 pages (1,202,622 bytes) |
| Courts identified / cases | 8 courts (azd, ca1, ca10, ca2, ca7, cacd, cand, cod) / 13 cases |
| Case number found | 13 of 13 |
| Case numbers equal across two independent PDF readers (poppler vs pdfminer.six) | 13 of 13 |
| Stamp fields (court, document number) equal to those encoded in RECAP file names | 11 of 11 compared |
| Court from page text / from file name / unresolved | 9 / 1 / 3 |
| Document number from stamp / from file name / unresolved | 9 / 2 / 2 |
| Filing date read from stamp | 9 of 13 |
| Filings complete / partial excerpts / completeness unknown | 3 / 4 / 6 |
| Pages read from text layer / by OCR | 37 / 1 (1.413 s of OCR) |
| Document types | Order 4, Excerpt 3, Unclassified 2, Complaint 1, Minutes 1, Notice 1, Opinion 1 |
| Document type equal to hand label | 12 of 13 |
| Files filed with no open question / flagged for review | 6 / 7 |
| Planted errors caught by the checks | 2 of 2 |
| Organised copies byte-identical (SHA-256) | 13 of 13 |
| Automated tests | 44 passed, 0 failed, 0 errors, 0 skipped (3.017 s) |
| Personal-data screen: flagged / cleared by manual review | 1 / 1 |
| Stage seconds | read + OCR 1.592; organise 0.004; report 0.0; verify 1.383; workbook 0.022 |
| Total seconds, throughput | 3.004 s; 4.33 documents/s, 12.65 pages/s |

Durations are one measured run on one machine (Python 3.12.3, poppler 24.02.0, Tesseract 5.3.4, recorded 2026-10-21T09:14:30+00:00) and vary by machine.

## Reproduce the run

System tools: Python 3.10+ with `venv`, `pdftotext` (poppler-utils) and `tesseract` (tesseract-ocr).

```bash
bash reproduce.sh
```

This creates a virtual environment, installs the pinned dependencies, downloads the pinned input files and verifies their SHA-256 checksums, runs the toolkit, runs the tests, and writes everything to `proof/`. To use the toolkit on your own folder:

```bash
PYTHONPATH=src python -m courtfile run --input path/to/pdfs --output path/to/output --log run.log
```

Rebuild the portfolio images (optional): `pip install -r portfolio/requirements-portfolio.txt && playwright install chromium && python scripts/build_readme.py && python portfolio/build_images.py && python portfolio/export_images.py`.

## How the results were checked

- **File-name check.** Court and document number read from the page stamp must equal those encoded in RECAP-style file names, an independent source, wherever both exist.
- **Two-reader check.** The stamp parsed from poppler text must equal the stamp parsed from pdfminer.six text. In the 2 disagreements the strict parser returned "not readable" while the second reader returned a value; for `gov.uscourts.cand.203070.27.0.pdf` the file name shows the second reader's document number was wrong, which is why the toolkit routes such stamps to review.
- **Hand labels.** Document types are compared with labels assigned by reading page 1 (`reference/reference_labels.csv`). Miss: `xray__no_bad_redactions.4.1.pdf` (predicted Unclassified, hand label Jury note).
- **Copy integrity and reconciliation.** Every organised file is hashed against its source; input PDFs, index rows and organised files must all be equal in number.
- **The checks can fail.** `planted_error_selftest` corrupts a label and a file-name value on purpose and confirms that each check reports it (2 of 2 caught).
- **Personal-data screen.** Every document, including OCR text, is scanned for email addresses, telephone numbers, SSN-like numbers and street/ZIP lines. Flagged documents need a recorded manual decision (`reference/pii_review.csv`) or the tests fail.

## Honest limits of the numbers

- The input is 13 public filings that Free Law Project distributes as open test files. Several are deliberately awkward (interior pages cut from longer filings, an overprinted stamp, a scanned page), so the set is a stress sample, not a representative client collection. No claim is made about accuracy or speed on other collections; 3.004 s is the time for this set on this machine.
- The classification rules were written while looking at these same files and the hand labels were assigned by the author, so 12/13 is a development-set score and not an estimate of accuracy on new documents.
- The file-name check covers only files whose names encode a court and document number; the two-reader check shows agreement between two readers, not correctness against an external answer key.
- Court ids come from the page text. Interior pages do not name their court, so 3 files are filed under `_court-unresolved`.
- The bankruptcy stamp pattern is covered by a unit test on a stamp line copied from a filing that was left out of the corpus (an individual debtor's case); no bankruptcy filing is in the measured set.
- The toolkit works on PDFs that are already on disk and reports on identification, classification, filing and indexing only.
- The index records no party names. The PDFs themselves are public court records that name parties and are not redistributed here.

## Data source

Real public federal-court PDFs, pinned by commit and checksum in `corpus.lock.json` (retrieved 2026-10-21). Licence of the source repositories: BSD-2-Clause (repository licence of freelawproject/doctor and freelawproject/x-ray). Run `python scripts/fetch_corpus.py` to download and verify them; the PDFs are not committed.

- https://github.com/freelawproject/doctor at commit `cce98c25f5bcf4b7340b33c5d81cfb2466624b4e`
- https://github.com/freelawproject/x-ray at commit `4dd5b0bcc5cdd774b9e82fc47b1d7208e92e4779`

29 further candidates from the same repositories were examined and excluded (reason recorded per file under `excluded` in the lock file): contact details of individuals found by the personal-data screen, test files whose names state that redacted text is recoverable, non-court files, personal financial records, and filings about sensitive personal matters.

| Local name | Path in source repository | SHA-256 (first 16) |
|---|---|---|
| `doctor__ca10_010110462922.pdf` | `doctor/test_assets/recap_documents/ca10_010110462922.pdf` | `280be3c8c9ef2458…` |
| `doctor__ca1_00117684624.pdf` | `doctor/test_assets/recap_documents/ca1_00117684624.pdf` | `9d81ff550ec8d851…` |
| `doctor__ca2_1-1.pdf` | `doctor/test_assets/recap_documents/ca2_1-1.pdf` | `a4b93b8b90632958…` |
| `doctor__ca7_3.pdf` | `doctor/test_assets/recap_documents/ca7_3.pdf` | `ffd9b75c84a63973…` |
| `doctor__gov.uscourts.azd.1085839.3.0.pdf` | `doctor/test_assets/recap_extract/gov.uscourts.azd.1085839.3.0.pdf` | `3504c832ec6845f3…` |
| `doctor__gov.uscourts.cacd.652774.40.0.pdf` | `doctor/test_assets/recap_extract/gov.uscourts.cacd.652774.40.0.pdf` | `44e06abc9865b008…` |
| `doctor__gov.uscourts.cand.203070.27.0.pdf` | `doctor/test_assets/recap_extract/gov.uscourts.cand.203070.27.0.pdf` | `99101de2343b531b…` |
| `xray__multi_line_redaction_ok.pdf` | `tests/assets/multi_line_redaction_ok.pdf` | `82c223c84cd591a6…` |
| `xray__no_bad_redactions.4.1.pdf` | `tests/assets/no_bad_redactions.4.1.pdf` | `1933de77c0bd0c8d…` |
| `xray__no_bad_redactions.6.2.pdf` | `tests/assets/no_bad_redactions.6.2.pdf` | `f5c7b1ef970a6085…` |
| `xray__rect_ordering_0.8.pdf` | `tests/assets/rect_ordering_0.8.pdf` | `ddb9e890915cbdbf…` |
| `xray__rect_ordering_4.1.pdf` | `tests/assets/rect_ordering_4.1.pdf` | `3f8e34d05f9388c6…` |
| `xray__rectangles_no.pdf` | `tests/assets/rectangles_no.pdf` | `79fc25180b27593a…` |

## File map

```
src/courtfile/      stamps.py, courts.py, extract.py, classify.py, organize.py, report.py, verify.py, pipeline.py
tests/              44 automated tests (unit tests and integration tests on the pinned corpus)
scripts/            fetch_corpus.py, make_lock.py, record_env.py, summarise_tests.py, build_readme.py
reference/          reference_labels.csv (hand labels), pii_review.csv (manual personal-data decisions)
corpus.lock.json    pinned source URLs, commits, checksums, exclusions
reproduce.sh        one command for the whole run
proof/              run.log, fetch.log, outputs/ (case_index.xlsx, case_index.csv, results.json, records.json,
                    case_files.tree.txt), pytest.txt, pytest-junit.xml, test-summary.json, env.json
portfolio/          the five image HTML files, build and export scripts, exports, entry sheet, DELIVERY-NOTES.md
```

The organised PDF copies are produced by `reproduce.sh` under `proof/outputs/case_files/` and are not committed; `proof/outputs/case_files.tree.txt` lists them.

## Credits and licences

- **Data:** Free Law Project test files (BSD-2-Clause repositories listed above); the documents are public court records.
- **Fonts (images):** Newsreader (SIL Open Font License 1.1) and IBM Plex Mono (SIL Open Font License 1.1); notices in `portfolio/fonts/`.
- **Libraries:** pdfminer.six (MIT), pypdfium2 (Apache-2.0 or BSD-3-Clause), pytesseract (Apache-2.0), Pillow (MIT-CMU), openpyxl (MIT), pytest (MIT), Playwright for Python (Apache-2.0). External programs: poppler `pdftotext` (GPL) and Tesseract (Apache-2.0), called as separate processes.
- No licence has been chosen for the toolkit's own code; add one before inviting reuse.
