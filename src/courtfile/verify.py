"""Independent checks on a run, each able to fail, plus a planted-error self-test.

1. filename vs text   - court and document number read from the page stamp must equal those encoded in
                        RECAP-style file names (an independent source) wherever both exist.
2. extractor agreement - the stamp parsed from poppler text must equal the stamp parsed from a second,
                        unrelated extractor (pdfminer.six).
3. reference labels   - document types predicted by the classifier vs. hand-assigned labels.
4. copy integrity     - every organised file is byte-identical (SHA-256) to its source.
5. reconciliation     - rows in the CSV, organised files and input PDFs all agree.
"""
from __future__ import annotations

import csv
import hashlib
import os

from .extract import pdfminer_pages
from .stamps import parse_stamp


def load_reference(reference_dir: str | None) -> dict[str, str]:
    if not reference_dir:
        return {}
    path = os.path.join(reference_dir, "reference_labels.csv")
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {row["filename"]: row["doc_type"] for row in csv.DictReader(fh)}


def load_pii_review(reference_dir: str | None) -> set[str]:
    """File names a human has reviewed after the screen flagged them and decided to retain."""
    if not reference_dir:
        return set()
    path = os.path.join(reference_dir, "pii_review.csv")
    if not os.path.exists(path):
        return set()
    with open(path, newline="", encoding="utf-8") as fh:
        return {row["filename"] for row in csv.DictReader(fh) if row["decision"] == "retain"}


def compare_filename_vs_text(records: list[dict]) -> dict:
    compared = agree = 0
    mismatches = []
    for rec in records:
        for field, text_value in (("court", rec["court_text"]), ("doc_number", rec["doc_number_text"])):
            hint = rec["hints"].get(field)
            if hint is None or text_value is None:
                continue
            compared += 1
            if str(hint) == str(text_value):
                agree += 1
            else:
                mismatches.append({"file": rec["filename"], "field": field, "filename": hint, "text": text_value})
    return {"fields_compared": compared, "agree": agree, "mismatches": mismatches}


def compare_labels(records: list[dict], reference: dict[str, str]) -> dict:
    scored = [r for r in records if r["filename"] in reference]
    wrong = [{"file": r["filename"], "predicted": r["doc_type"], "reference": reference[r["filename"]]}
             for r in scored if r["doc_type"] != reference[r["filename"]]]
    return {"documents_scored": len(scored), "correct": len(scored) - len(wrong), "misses": wrong}


def cross_extractor(records: list[dict], paths: list[str]) -> dict:
    agree = compared = case_agree = 0
    disagreements = []
    by_name = {os.path.basename(p): p for p in paths}
    for rec in records:
        try:
            second = parse_stamp(pdfminer_pages(by_name[rec["filename"]])[0])
        except Exception as exc:  # extractor failure counts as a disagreement, not a crash
            disagreements.append({"file": rec["filename"], "reason": f"second extractor failed: {exc}"})
            compared += 1
            continue
        a = (rec["case_number"], rec["doc_number_text"], rec["filed"])
        b = (second.case_number, second.doc_number, second.filed) if second else (None, None, None)
        compared += 1
        case_agree += int(a[0] == b[0])
        if a == b:
            agree += 1
        else:
            disagreements.append({"file": rec["filename"], "poppler": list(a), "pdfminer": list(b)})
    return {"documents_compared": compared, "agree": agree, "case_number_agree": case_agree,
            "disagreements": disagreements}


def copy_integrity(records: list[dict], output_dir: str) -> dict:
    bad = []
    for rec in records:
        path = os.path.join(output_dir, "case_files", rec["new_path"])
        with open(path, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != rec["sha256"]:
                bad.append(rec["new_path"])
    return {"files_checked": len(records), "mismatches": bad}


def reconcile(records: list[dict], paths: list[str], output_dir: str) -> dict:
    with open(os.path.join(output_dir, "case_index.csv"), newline="", encoding="utf-8") as fh:
        csv_rows = sum(1 for _ in csv.reader(fh)) - 1
    organised = sum(len(files) for _, _, files in os.walk(os.path.join(output_dir, "case_files")))
    return {"input_pdfs": len(paths), "records": len(records), "csv_rows": csv_rows,
            "organised_files": organised,
            "consistent": len({len(paths), len(records), csv_rows, organised}) == 1}


def planted_error_selftest(records: list[dict], reference: dict[str, str]) -> dict:
    """Corrupt known-good inputs on purpose and confirm that each check reports the corruption."""
    caught = 0
    planted = 0
    # (a) flip one reference label
    if reference:
        name = next(iter(reference))
        tampered = dict(reference)
        tampered[name] = "Not-A-Real-Type"
        planted += 1
        caught += int(len(compare_labels(records, tampered)["misses"]) > len(compare_labels(records, reference)["misses"]))
    # (b) corrupt one filename-derived document number
    candidates = [r for r in records if r["hints"].get("doc_number") and r["doc_number_text"]]
    if candidates:
        import copy
        tampered_records = copy.deepcopy(records)
        target = next(r for r in tampered_records if r["filename"] == candidates[0]["filename"])
        target["hints"]["doc_number"] = target["hints"]["doc_number"] + "9"
        planted += 1
        caught += int(len(compare_filename_vs_text(tampered_records)["mismatches"])
                      > len(compare_filename_vs_text(records)["mismatches"]))
    return {"errors_planted": planted, "errors_caught": caught}


def verify_run(records: list[dict], input_dir: str, output_dir: str, reference_dir: str | None, paths: list[str]) -> dict:
    reference = load_reference(reference_dir)
    return {
        "filename_vs_text": compare_filename_vs_text(records),
        "reference_labels": compare_labels(records, reference),
        "cross_extractor": cross_extractor(records, paths),
        "copy_integrity": copy_integrity(records, output_dir),
        "reconciliation": reconcile(records, paths, output_dir),
        "planted_error_selftest": planted_error_selftest(records, reference),
    }
