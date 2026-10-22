# Delivery notes

## Palette and type

Navy ink signals institutional trust to legal-support buyers, warm paper evokes the archival record, and a single amber accent works like a highlighter on the figures a reviewer should read first; the six text and background pairs measure 5.61:1 or better (WCAG), against a requirement of 4.5:1. Newsreader (editorial serif) carries headlines and figures, IBM Plex Mono carries identifiers, file names and labels. Every board shares a 1280 x 960 artboard, a 48 px ruled baseline, one margin rule and a 960 x 720 core, and differs in composition.

## Images: file, design rationale, provenance

| # | File | Design rationale | Provenance (files under `proof/outputs/` unless noted) |
|---|---|---|---|
| 1 | `1-federal-court-pdf-indexer-python-outcome` | A typographic monolith: one amber figure dominates the board, and a slightly rotated stamp assembled from the real complaint's header fields is the only ornament. | `results.json`: verification.cross_extractor.case_number_agree and documents_compared, corpus.documents, corpus.courts, run_seconds; `records.json`: the Complaint record (case_number, doc_number, filed, stamp_page, stamp_total) from `xray__rectangles_no.pdf`. |
| 2 | `2-court-pdf-organiser-before-after` | A before-and-after ledger on ruled paper that sets the real input file names against the court/case folders built from them, with flagged rows in the accent colour. | `records.json`: filename, new_path, doc_type and status of all 13 records; source files are the 13 PDFs pinned in `corpus.lock.json`. |
| 3 | `3-court-pdf-automation-pipeline-timing` | A shared-axis timeline in which each stage's bar starts where the previous one ended, so the longest stages dominate honestly on a zero-based scale. | `results.json`: stage_seconds (five stages), run_seconds, corpus.documents, corpus.pages. |
| 4 | `4-court-document-classification-results` | A two-column, zero-based bar comparison that gives the reasons files were flagged the same visual weight as the document types that were found. | `results.json`: classification.by_type, review.needs_review, corpus.documents; `records.json`: review_reasons of every record. |
| 5 | `5-court-pdf-indexer-verified-tests` | A framed test-count panel beside a ledger of independent checks; the one imperfect result is shown as it is, without the accent colour. | `results.json`: verification.filename_vs_text, cross_extractor.case_number_agree, planted_error_selftest, copy_integrity, reference_labels; `test-summary.json`; `env.json` (python, poppler, Tesseract, pytest). |

Suggested upload names are the file names above (keyword-rich, `.png` masters and `.jpg` copies).

## Omissions

- No party names, attorney names or case captions appear anywhere in the images or the index (personal-data rule). Case numbers and court ids do appear; they are public identifiers.
- Retrieval from court systems, docket-sheet research and party or claim extraction from complaints were not built or claimed: this environment could not exercise retrieval, and the pinned set holds a single complaint page, too little to measure extraction.
- No before/after human-time comparison, scale test or accuracy claim for other collections: nothing of the kind was measured.
- The three files whose court is not named on the page, the two without a readable document number and the four without a readable filing date are shown as flagged, not filled in.
- No upload copies were needed: the largest JPG master is under 5 MB.
- No client, testimonial, review or user count is shown or implied.
- No licence was chosen for the toolkit's own code (README says so).
- Upwork's help page states title 70, role 100, description 600 characters and five skill tags; its file-size table is an image I could not read, so the brief's 5 MB limit was used. Third-party sites quote different limits; the official page was followed.

## Audit

| Requirement | How it was checked | Measured outcome |
|---|---|---|
| Input data is real, sourced, licensed, checksummed | `corpus.lock.json` pins URL, commit and SHA-256; clean-directory run downloaded and verified every file | 13 files verified, 0 checksum failures |
| No personal data about individuals; nothing redistributed that may not be | candidates screened on their text layer before selection; the kept set re-screened on text plus OCR text (this caught one attorney appearance form, which was then excluded); manual decision recorded; PDFs are not committed or zipped | 29 candidates excluded; 1 flagged in the kept set, manually cleared (institutional contact details) |
| Working, tested solution with one reproduction command | `bash reproduce.sh` executed in an empty directory after unzipping | exit code 0; 44 of 44 tests passed |
| Correctness figures reproduce | results.json from the clean run compared with the primary run, duration fields excluded | identical |
| Independent verification that can fail | file-name check, second PDF reader, hand labels, planted errors | 2 of 2 planted errors caught; one hand-label miss reported, not hidden |
| Environment and per-stage durations recorded | `proof/env.json`, `results.json` stage_seconds | Python 3.12.3, Tesseract 5.3.4, five stage timings |
| Every figure in the images traces to the run | `audit_images.py` extracts the visible numbers of each image and looks each up in the results files | numbers not found: 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 |
| Zip layout | listed the zip's entries | single top-level folder `pacer-court-pdf-case-file-indexer` |
| Push command paths valid | ran the first line (unzip, cd) and, in a temporary clone, `git init`, `git add`, `git commit`; `gh` was not run | 62 files tracked; 4000 x 3000 exports tracked: 0; court PDFs tracked: 0; untracked left over: 0 |
| Artboard 4:3, 1280 x 960 authored, exported 4000 x 3000 | re-opened every exported file | all 10 files 4000 x 3000 (table below) |
| 300 DPI, sRGB profile embedded, JPG 4:4:4, size | read from the exported files | all PNG and JPG: 300 DPI tag, sRGB profile, JPG 4:4:4, largest JPG 2.67 MB |
| Safe zone (70 px) and central 960 x 720 region | bounding boxes measured in the rendered page | elements outside the safe zone: 0; outside the central region: 0 |
| Text fits, nothing overflows or collides | scrollWidth test on every element and headline/stamp overlap test | overflowing elements: 0; overlaps: 0; smallest text 16 px (footers) |
| Intended fonts rendered, not fallbacks | FontFace status read in Chromium | Newsreader 400/500/400 italic and IBM Plex Mono 400/500: all `loaded` |
| No JavaScript, external resources, URLs, emails or phone numbers in the artwork | HTML scan and visible-text scan | script tags 0, external resources 0, URL-like text 0, emails 0, phones 0; repository URL only in the leading HTML comment |
| Contrast | WCAG ratios calculated in `build_images.py` | lowest of six pairs 5.61:1 (all at least 4.5:1) |
| Thumbnail legibility | rendered each image at 300 px wide (`portfolio/thumbs/`) and inspected them | headline and key figure legible in all five; footers are decorative at that size (judged by eye) |

Exported files, as measured by re-opening them:

| Image | Pixels | DPI (PNG / JPG) | Profile | JPG chroma | Bytes (PNG / JPG) |
|---|---|---|---|---|---|
| `1-federal-court-pdf-indexer-python-outcome` | 4000 x 3000 | 300 / 300 | sRGB built-in | 4:4:4 | 306,946 / 1,728,568 |
| `2-court-pdf-organiser-before-after` | 4000 x 3000 | 300 / 300 | sRGB built-in | 4:4:4 | 451,837 / 2,672,541 |
| `3-court-pdf-automation-pipeline-timing` | 4000 x 3000 | 300 / 300 | sRGB built-in | 4:4:4 | 294,115 / 1,608,298 |
| `4-court-document-classification-results` | 4000 x 3000 | 300 / 300 | sRGB built-in | 4:4:4 | 247,184 / 1,748,017 |
| `5-court-pdf-indexer-verified-tests` | 4000 x 3000 | 300 / 300 | sRGB built-in | 4:4:4 | 321,336 / 1,782,959 |

The clean-directory verification above ran on the package that is identical to this one except for this file and `proof/clean-room-verification.json`. Durations in the clean run: total 3.341 s (the figures in the images are from the primary run, 3.004 s); they vary by machine.

## Re-export the images

1. `pip install -r portfolio/requirements-portfolio.txt && playwright install chromium`
2. `python portfolio/build_images.py` regenerates the five HTML files from `proof/`.
3. `python portfolio/export_images.py` renders each at a 1280 x 960 viewport and device scale factor 3.125 (exactly 4000 x 3000), writes a lossless PNG and a JPG at quality 100 with 4:4:4 chroma, both at 300 DPI with an embedded sRGB profile, and writes `export-report.json` (dimensions, DPI, profile, chroma, size, zone and overflow measurements).
4. `python portfolio/audit_images.py` repeats the rule and provenance audit.
5. Any JPG over 5 MB would need a re-encode at the highest quality that fits; none does now.
