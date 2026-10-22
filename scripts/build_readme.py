"""Write README.md. Every number in the results table is read from proof/outputs/results.json,
proof/test-summary.json, proof/env.json and corpus.lock.json; only the prose is typed."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
res = json.loads((ROOT / "proof/outputs/results.json").read_text())
tests = json.loads((ROOT / "proof/test-summary.json").read_text())
env = json.loads((ROOT / "proof/env.json").read_text())
lock = json.loads((ROOT / "corpus.lock.json").read_text())
REPO = "pacer-court-pdf-case-file-indexer"
URL = f"https://github.com/alif777asif-wq/{REPO}"

c, e, i, cl, rv = res["corpus"], res["extraction"], res["identification"], res["classification"], res["review"]
v = res["verification"]
ce, fv, ps, ci, rl = v["cross_extractor"], v["filename_vs_text"], v["planted_error_selftest"], v["copy_integrity"], v["reference_labels"]
st = res["stage_seconds"]
miss = ", ".join(f"`{m['file']}` (predicted {m['predicted']}, hand label {m['reference']})" for m in rl["misses"])
types = ", ".join(f"{k} {n}" for k, n in sorted(cl["by_type"].items(), key=lambda kv: (-kv[1], kv[0])))

table = f"""| Measure | Result (one measured run) |
|---|---|
| Documents / pages processed | {c['documents']} PDFs / {c['pages']} pages ({c['bytes']:,} bytes) |
| Courts identified / cases | {len(c['courts'])} courts ({', '.join(c['courts'])}) / {c['cases']} cases |
| Case number found | {i['case_number_found']} of {c['documents']} |
| Case numbers equal across two independent PDF readers (poppler vs pdfminer.six) | {ce['case_number_agree']} of {ce['documents_compared']} |
| Stamp fields (court, document number) equal to those encoded in RECAP file names | {fv['agree']} of {fv['fields_compared']} compared |
| Court from page text / from file name / unresolved | {i['court_from_text']} / {i['court_from_filename']} / {i['court_unresolved']} |
| Document number from stamp / from file name / unresolved | {i['doc_number_from_text']} / {i['doc_number_from_filename']} / {i['doc_number_unresolved']} |
| Filing date read from stamp | {i['filing_date_found']} of {c['documents']} |
| Filings complete / partial excerpts / completeness unknown | {i['complete_filings']} / {i['partial_excerpts']} / {i['completeness_unknown']} |
| Pages read from text layer / by OCR | {e['pages_with_text_layer']} / {e['pages_ocr']} ({e['ocr_seconds']} s of OCR) |
| Document types | {types} |
| Document type equal to hand label | {rl['correct']} of {rl['documents_scored']} |
| Files filed with no open question / flagged for review | {rv['ok']} / {rv['needs_review']} |
| Planted errors caught by the checks | {ps['errors_caught']} of {ps['errors_planted']} |
| Organised copies byte-identical (SHA-256) | {ci['files_checked'] - len(ci['mismatches'])} of {ci['files_checked']} |
| Automated tests | {tests['passed']} passed, {tests['failures']} failed, {tests['errors']} errors, {tests['skipped']} skipped ({tests['seconds']} s) |
| Personal-data screen: flagged / cleared by manual review | {res['personal_data_screen']['documents_flagged']} / {len(res['personal_data_screen']['flagged_and_manually_cleared'])} |
| Stage seconds | {'; '.join(f'{k[2:]} {val}' for k, val in st.items())} |
| Total seconds, throughput | {res['run_seconds']} s; {res['throughput']['documents_per_second']} documents/s, {res['throughput']['pages_per_second']} pages/s |

Durations are one measured run on one machine (Python {env['python']}, poppler {env['poppler_pdftotext'].split()[-1]}, Tesseract {env['tesseract'].split()[-1]}, recorded {env['recorded_at']}) and vary by machine."""

lock_rows = "\n".join(f"| `{f['local_name']}` | `{f['path_in_repo']}` | `{f['sha256'][:16]}…` |" for f in lock["files"])
repos = sorted({(f["source_repo"], f["commit"]) for f in lock["files"]})
repo_lines = "\n".join(f"- {r} at commit `{sha}`" for r, sha in repos)
excluded_n = len(lock["excluded"])

readme = f"""# PACER court PDF case-file indexer

A Python toolkit that turns a folder of federal court PDFs into an identified, classified, organised and indexed case file. It was built and tested as an original, independent project; there is no client behind it.

Repository: {URL}

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

{table}

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
- **Two-reader check.** The stamp parsed from poppler text must equal the stamp parsed from pdfminer.six text. In the {len(ce['disagreements'])} disagreements the strict parser returned "not readable" while the second reader returned a value; for `gov.uscourts.cand.203070.27.0.pdf` the file name shows the second reader's document number was wrong, which is why the toolkit routes such stamps to review.
- **Hand labels.** Document types are compared with labels assigned by reading page 1 (`reference/reference_labels.csv`). Miss: {miss or 'none'}.
- **Copy integrity and reconciliation.** Every organised file is hashed against its source; input PDFs, index rows and organised files must all be equal in number.
- **The checks can fail.** `planted_error_selftest` corrupts a label and a file-name value on purpose and confirms that each check reports it ({ps['errors_caught']} of {ps['errors_planted']} caught).
- **Personal-data screen.** Every document, including OCR text, is scanned for email addresses, telephone numbers, SSN-like numbers and street/ZIP lines. Flagged documents need a recorded manual decision (`reference/pii_review.csv`) or the tests fail.

## Honest limits of the numbers

- The input is {c['documents']} public filings that Free Law Project distributes as open test files. Several are deliberately awkward (interior pages cut from longer filings, an overprinted stamp, a scanned page), so the set is a stress sample, not a representative client collection. No claim is made about accuracy or speed on other collections; {res['run_seconds']} s is the time for this set on this machine.
- The classification rules were written while looking at these same files and the hand labels were assigned by the author, so {rl['correct']}/{rl['documents_scored']} is a development-set score and not an estimate of accuracy on new documents.
- The file-name check covers only files whose names encode a court and document number; the two-reader check shows agreement between two readers, not correctness against an external answer key.
- Court ids come from the page text. Interior pages do not name their court, so {i['court_unresolved']} files are filed under `_court-unresolved`.
- The bankruptcy stamp pattern is covered by a unit test on a stamp line copied from a filing that was left out of the corpus (an individual debtor's case); no bankruptcy filing is in the measured set.
- The toolkit works on PDFs that are already on disk and reports on identification, classification, filing and indexing only.
- The index records no party names. The PDFs themselves are public court records that name parties and are not redistributed here.

## Data source

Real public federal-court PDFs, pinned by commit and checksum in `corpus.lock.json` (retrieved {lock['retrieved']}). Licence of the source repositories: {lock['licence']}. Run `python scripts/fetch_corpus.py` to download and verify them; the PDFs are not committed.

{repo_lines}

{excluded_n} further candidates from the same repositories were examined and excluded (reason recorded per file under `excluded` in the lock file): contact details of individuals found by the personal-data screen, test files whose names state that redacted text is recoverable, non-court files, personal financial records, and filings about sensitive personal matters.

| Local name | Path in source repository | SHA-256 (first 16) |
|---|---|---|
{lock_rows}

## File map

```
src/courtfile/      stamps.py, courts.py, extract.py, classify.py, organize.py, report.py, verify.py, pipeline.py
tests/              {tests['tests']} automated tests (unit tests and integration tests on the pinned corpus)
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
"""
(ROOT / "README.md").write_text(readme, encoding="utf-8")
print("README.md written,", len(readme), "characters")
