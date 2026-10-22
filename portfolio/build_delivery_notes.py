"""Write portfolio/DELIVERY-NOTES.md from the measured reports: rationale, provenance, omissions, audit, re-export steps."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
J = lambda p: json.loads((ROOT / p).read_text())
res, build, exp, aud = J("proof/outputs/results.json"), J("portfolio/build-report.json"), J("portfolio/export-report.json"), J("portfolio/audit-report.json")
tests, env, clean = J("proof/test-summary.json"), J("proof/env.json"), J("proof/clean-room-verification.json")
V = res["verification"]
names = build["boards"]
ratios = build["contrast_ratios"]
exports = [k for k in exp if not k.startswith("_")]

rationale = [
    "A typographic monolith: one amber figure dominates the board, and a slightly rotated stamp assembled from the real complaint's header fields is the only ornament.",
    "A before-and-after ledger on ruled paper that sets the real input file names against the court/case folders built from them, with flagged rows in the accent colour.",
    "A shared-axis timeline in which each stage's bar starts where the previous one ended, so the longest stages dominate honestly on a zero-based scale.",
    "A two-column, zero-based bar comparison that gives the reasons files were flagged the same visual weight as the document types that were found.",
    "A framed test-count panel beside a ledger of independent checks; the one imperfect result is shown as it is, without the accent colour.",
]
provenance = [
    "`results.json`: verification.cross_extractor.case_number_agree and documents_compared, corpus.documents, corpus.courts, run_seconds; `records.json`: the Complaint record (case_number, doc_number, filed, stamp_page, stamp_total) from `xray__rectangles_no.pdf`.",
    "`records.json`: filename, new_path, doc_type and status of all 13 records; source files are the 13 PDFs pinned in `corpus.lock.json`.",
    "`results.json`: stage_seconds (five stages), run_seconds, corpus.documents, corpus.pages.",
    "`results.json`: classification.by_type, review.needs_review, corpus.documents; `records.json`: review_reasons of every record.",
    "`results.json`: verification.filename_vs_text, cross_extractor.case_number_agree, planted_error_selftest, copy_integrity, reference_labels; `test-summary.json`; `env.json` (python, poppler, Tesseract, pytest).",
]
omissions = [
    "No party names, attorney names or case captions appear anywhere in the images or the index (personal-data rule). Case numbers and court ids do appear; they are public identifiers.",
    "Retrieval from court systems, docket-sheet research and party or claim extraction from complaints were not built or claimed: this environment could not exercise retrieval, and the pinned set holds a single complaint page, too little to measure extraction.",
    "No before/after human-time comparison, scale test or accuracy claim for other collections: nothing of the kind was measured.",
    "The three files whose court is not named on the page, the two without a readable document number and the four without a readable filing date are shown as flagged, not filled in.",
    "No upload copies were needed: the largest JPG master is under 5 MB.",
    "No client, testimonial, review or user count is shown or implied.",
    "No licence was chosen for the toolkit's own code (README says so).",
    "Upwork's help page states title 70, role 100, description 600 characters and five skill tags; its file-size table is an image I could not read, so the brief's 5 MB limit was used. Third-party sites quote different limits; the official page was followed.",
]


def row(req, how, out):
    return f"| {req} | {how} | {out} |"


files_tbl = "\n".join(
    f"| `{k}` | {exp[k]['png']['width']} x {exp[k]['png']['height']} | {exp[k]['png']['dpi_tag'][0]} / {exp[k]['jpg']['dpi_tag'][0]} | {exp[k]['png']['icc_profile']} | {exp[k]['jpg']['chroma_subsampling']} | {exp[k]['png']['bytes']:,} / {exp[k]['jpg']['bytes']:,} |"
    for k in exports)
audit = [
    row("Input data is real, sourced, licensed, checksummed", "`corpus.lock.json` pins URL, commit and SHA-256; clean-directory run downloaded and verified every file", f"{res['corpus']['documents']} files verified, 0 checksum failures"),
    row("No personal data about individuals; nothing redistributed that may not be", "candidates screened on their text layer before selection; the kept set re-screened on text plus OCR text (this caught one attorney appearance form, which was then excluded); manual decision recorded; PDFs are not committed or zipped", f"{len(json.loads((ROOT / 'corpus.lock.json').read_text())['excluded'])} candidates excluded; {res['personal_data_screen']['documents_flagged']} flagged in the kept set, manually cleared (institutional contact details)"),
    row("Working, tested solution with one reproduction command", "`bash reproduce.sh` executed in an empty directory after unzipping", f"exit code {clean['reproduce_exit_code']}; {clean['tests']['passed']} of {clean['tests']['tests']} tests passed"),
    row("Correctness figures reproduce", "results.json from the clean run compared with the primary run, duration fields excluded", "identical" if clean["correctness_fields_identical_to_primary_run"] else "DIFFERENT"),
    row("Independent verification that can fail", "file-name check, second PDF reader, hand labels, planted errors", f"{V['planted_error_selftest']['errors_caught']} of {V['planted_error_selftest']['errors_planted']} planted errors caught; one hand-label miss reported, not hidden"),
    row("Environment and per-stage durations recorded", "`proof/env.json`, `results.json` stage_seconds", f"Python {env['python']}, Tesseract {env['tesseract'].split()[-1]}, five stage timings"),
    row("Every figure in the images traces to the run", "`audit_images.py` extracts the visible numbers of each image and looks each up in the results files", "numbers not found: " + ", ".join(f"{k.split('-')[0]}: {len(v['numbers_not_found_in_results'])}" for k, v in aud.items())),
    row("Zip layout", "listed the zip's entries", f"single top-level folder `{clean['zip_top_level_folders'][0]}`"),
    row("Push command paths valid", "ran the first line (unzip, cd) and, in a temporary clone, `git init`, `git add`, `git commit`; `gh` was not run", f"{clean['git_tracked_files']} files tracked; 4000 x 3000 exports tracked: {clean['git_tracked_4000x3000_exports']}; court PDFs tracked: {clean['git_tracked_court_pdfs']}; untracked left over: {clean['git_untracked_after_commit']}"),
    row("Artboard 4:3, 1280 x 960 authored, exported 4000 x 3000", "re-opened every exported file", "all 10 files 4000 x 3000 (table below)"),
    row("300 DPI, sRGB profile embedded, JPG 4:4:4, size", "read from the exported files", "all PNG and JPG: 300 DPI tag, sRGB profile, JPG 4:4:4, largest JPG " + f"{max(exp[k]['jpg']['bytes'] for k in exports) / 1e6:.2f} MB"),
    row("Safe zone (70 px) and central 960 x 720 region", "bounding boxes measured in the rendered page", "elements outside the safe zone: " + str(sum(len(exp[k]['outside_safe_zone']) for k in exports)) + "; outside the central region: " + str(sum(len(exp[k]['outside_core_zone']) for k in exports))),
    row("Text fits, nothing overflows or collides", "scrollWidth test on every element and headline/stamp overlap test", "overflowing elements: " + str(sum(len(exp[k]['overflowing_elements']) for k in exports)) + "; overlaps: " + str(sum(len(exp[k]['overlaps']) for k in exports)) + f"; smallest text {min(exp[k]['smallest_text_px'] for k in exports):g} px (footers)"),
    row("Intended fonts rendered, not fallbacks", "FontFace status read in Chromium", "Newsreader 400/500/400 italic and IBM Plex Mono 400/500: all `loaded`"),
    row("No JavaScript, external resources, URLs, emails or phone numbers in the artwork", "HTML scan and visible-text scan", "script tags 0, external resources 0, URL-like text 0, emails 0, phones 0; repository URL only in the leading HTML comment"),
    row("Contrast", "WCAG ratios calculated in `build_images.py`", "lowest of six pairs " + f"{min(ratios.values())}:1 (all at least 4.5:1)"),
    row("Thumbnail legibility", "rendered each image at 300 px wide (`portfolio/thumbs/`) and inspected them", "headline and key figure legible in all five; footers are decorative at that size (judged by eye)"),
]
md = f"""# Delivery notes

## Palette and type

Navy ink signals institutional trust to legal-support buyers, warm paper evokes the archival record, and a single amber accent works like a highlighter on the figures a reviewer should read first; the six text and background pairs measure {min(ratios.values())}:1 or better (WCAG), against a requirement of 4.5:1. Newsreader (editorial serif) carries headlines and figures, IBM Plex Mono carries identifiers, file names and labels. Every board shares a 1280 x 960 artboard, a 48 px ruled baseline, one margin rule and a 960 x 720 core, and differs in composition.

## Images: file, design rationale, provenance

| # | File | Design rationale | Provenance (files under `proof/outputs/` unless noted) |
|---|---|---|---|
""" + "\n".join(f"| {i} | `{n}` | {r} | {p} |" for i, (n, r, p) in enumerate(zip(names, rationale, provenance), 1)) + f"""

Suggested upload names are the file names above (keyword-rich, `.png` masters and `.jpg` copies).

## Omissions

""" + "\n".join(f"- {o}" for o in omissions) + f"""

## Audit

| Requirement | How it was checked | Measured outcome |
|---|---|---|
""" + "\n".join(audit) + f"""

Exported files, as measured by re-opening them:

| Image | Pixels | DPI (PNG / JPG) | Profile | JPG chroma | Bytes (PNG / JPG) |
|---|---|---|---|---|---|
{files_tbl}

The clean-directory verification above ran on the package that is identical to this one except for this file and `proof/clean-room-verification.json`. Durations in the clean run: total {clean['durations_this_run']['run_seconds']} s (the figures in the images are from the primary run, {res['run_seconds']} s); they vary by machine.

## Re-export the images

1. `pip install -r portfolio/requirements-portfolio.txt && playwright install chromium`
2. `python portfolio/build_images.py` regenerates the five HTML files from `proof/`.
3. `python portfolio/export_images.py` renders each at a 1280 x 960 viewport and device scale factor 3.125 (exactly 4000 x 3000), writes a lossless PNG and a JPG at quality 100 with 4:4:4 chroma, both at 300 DPI with an embedded sRGB profile, and writes `export-report.json` (dimensions, DPI, profile, chroma, size, zone and overflow measurements).
4. `python portfolio/audit_images.py` repeats the rule and provenance audit.
5. Any JPG over 5 MB would need a re-encode at the highest quality that fits; none does now.
"""
(ROOT / "portfolio/DELIVERY-NOTES.md").write_text(md, encoding="utf-8")
print("DELIVERY-NOTES.md written,", len(md), "characters")
