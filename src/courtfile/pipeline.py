"""End-to-end run: ingest -> identify -> classify -> organise -> report, with per-stage timing."""
from __future__ import annotations

import contextlib
import glob
import json
import logging
import os
import time
from collections import Counter

from . import report, verify
from .classify import classify
from .courts import identify_court
from .extract import pii_counts, pdfminer_pages, read_pdf
from .organize import copy_tree, filename_hints, plan_paths
from .stamps import parse_stamp

LOG = logging.getLogger("courtfile.pipeline")


@contextlib.contextmanager
def stage(name: str, timings: dict):
    LOG.info("stage start: %s", name)
    t0 = time.perf_counter()
    yield
    timings[name] = time.perf_counter() - t0
    LOG.info("stage done: %s in %.3f s", name, timings[name])


def build_record(path: str, ocr: bool = True) -> dict:
    doc = read_pdf(path, ocr=ocr)
    page1 = doc.pages[0] if doc.pages else ""
    stamp = parse_stamp(page1)
    level = stamp.family if stamp and stamp.family != "caption" else None
    court_text = identify_court(page1, level)
    hints = filename_hints(path)
    doc_type, evidence = classify(page1, stamp.page if stamp else None)
    pii = pii_counts(doc.text)

    rec = {
        "filename": os.path.basename(path), "sha256": doc.sha256, "bytes": doc.size_bytes, "pages": doc.n_pages,
        "stamp_family": stamp.family if stamp else None,
        "case_number": stamp.case_number if stamp else None,
        "doc_number_text": stamp.doc_number if stamp else None,
        "court_text": court_text,
        "filed": stamp.filed if stamp else None,
        "stamp_page": stamp.page if stamp else None, "stamp_total": stamp.total_pages if stamp else None,
        "doc_type": doc_type, "doc_type_evidence": evidence,
        "ocr_pages": doc.ocr_pages, "ocr_seconds": doc.ocr_seconds,
        "text_chars": sum(len(p) for p in doc.pages), "pii_flags": sum(pii.values()),
        "text_source": "text layer" if not doc.ocr_pages else "text layer + OCR (p" + ",".join(map(str, doc.ocr_pages)) + ")",
        "hints": hints,
    }
    rec["court"] = court_text or hints.get("court")
    rec["court_source"] = "text" if court_text else ("filename" if hints.get("court") else None)
    rec["doc_number"] = rec["doc_number_text"] or hints.get("doc_number")
    rec["doc_number_source"] = "text" if rec["doc_number_text"] else ("filename" if hints.get("doc_number") else None)
    rec["is_complete"] = (doc.n_pages == rec["stamp_total"]) if rec["stamp_total"] else None

    reasons = []
    if not rec["case_number"]:
        reasons.append("case number not found")
    if not rec["court"]:
        reasons.append("court not named on the page")
    if not rec["doc_number"]:
        reasons.append("document number not readable")
    if not rec["filed"]:
        reasons.append("filing date not readable")
    if doc_type == "Unclassified":
        reasons.append("document type not recognised")
    rec["review_reasons"] = reasons
    rec["status"] = "ok" if not reasons else "review"
    return rec


def summarise(records: list[dict], timings: dict, total_seconds: float) -> dict:
    n_pages = sum(r["pages"] for r in records)
    return {
        "corpus": {
            "documents": len(records), "pages": n_pages, "bytes": sum(r["bytes"] for r in records),
            "courts": sorted({r["court"] for r in records if r["court"]}),
            "cases": len({r["case_number"] for r in records if r["case_number"]}),
        },
        "extraction": {
            "pages_with_text_layer": n_pages - sum(len(r["ocr_pages"]) for r in records),
            "pages_ocr": sum(len(r["ocr_pages"]) for r in records),
            "documents_needing_ocr": sum(1 for r in records if r["ocr_pages"]),
            "ocr_seconds": round(sum(r["ocr_seconds"] for r in records), 3),
        },
        "identification": {
            "stamp_families": dict(Counter(r["stamp_family"] or "none" for r in records)),
            "case_number_found": sum(1 for r in records if r["case_number"]),
            "court_from_text": sum(1 for r in records if r["court_source"] == "text"),
            "court_from_filename": sum(1 for r in records if r["court_source"] == "filename"),
            "court_unresolved": sum(1 for r in records if not r["court"]),
            "doc_number_from_text": sum(1 for r in records if r["doc_number_source"] == "text"),
            "doc_number_from_filename": sum(1 for r in records if r["doc_number_source"] == "filename"),
            "doc_number_unresolved": sum(1 for r in records if not r["doc_number"]),
            "filing_date_found": sum(1 for r in records if r["filed"]),
            "complete_filings": sum(1 for r in records if r["is_complete"] is True),
            "partial_excerpts": sum(1 for r in records if r["is_complete"] is False),
            "completeness_unknown": sum(1 for r in records if r["is_complete"] is None),
        },
        "classification": {
            "by_type": dict(sorted(Counter(r["doc_type"] for r in records).items())),
            "unclassified": sum(1 for r in records if r["doc_type"] == "Unclassified"),
        },
        "review": {"ok": sum(1 for r in records if r["status"] == "ok"),
                   "needs_review": sum(1 for r in records if r["status"] != "ok")},
        "personal_data_screen": {"documents_flagged": sum(1 for r in records if r["pii_flags"]),
                                 "flagged_names": sorted(r["filename"] for r in records if r["pii_flags"])},
        "stage_seconds": {k: round(v, 3) for k, v in timings.items()},
        "run_seconds": round(total_seconds, 3),
        "throughput": {"documents_per_second": round(len(records) / total_seconds, 2),
                       "pages_per_second": round(n_pages / total_seconds, 2)},
    }


def run(input_dir: str, output_dir: str, reference_dir: str | None = None, ocr: bool = True) -> dict:
    timings: dict[str, float] = {}
    t_start = time.perf_counter()
    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    paths = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))
    if not paths:
        raise SystemExit(f"no PDF files found in {input_dir}")
    os.makedirs(output_dir, exist_ok=True)
    LOG.info("found %d PDF files in %s", len(paths), input_dir)

    records: list[dict] = []
    with stage("1 read + OCR", timings):
        for path in paths:
            try:
                records.append(build_record(path, ocr=ocr))
            except Exception:  # one unreadable file must not stop the batch
                LOG.exception("could not process %s", path)
    with stage("2 organise", timings):
        plan_paths(records)
        copied = copy_tree(records, input_dir, os.path.join(output_dir, "case_files"))
    LOG.info("copied and verified %d files", copied)
    with stage("3 report", timings):
        report.write_csv(records, os.path.join(output_dir, "case_index.csv"))
    total = time.perf_counter() - t_start
    results = summarise(records, timings, total)
    with stage("4 verify", timings):
        results["verification"] = verify.verify_run(records, input_dir, output_dir, reference_dir, paths)
    results["stage_seconds"] = {k: round(v, 3) for k, v in timings.items()}
    reviewed = verify.load_pii_review(reference_dir)
    flagged = results["personal_data_screen"]["flagged_names"]
    results["personal_data_screen"]["flagged_and_manually_cleared"] = sorted(set(flagged) & reviewed)
    results["personal_data_screen"]["flagged_unreviewed"] = sorted(set(flagged) - reviewed)
    results["run"] = {"started": started, "input_dir": os.path.basename(input_dir.rstrip("/")),
                      "documents_unreadable": len(paths) - len(records)}
    flat = {"Documents": results["corpus"]["documents"], "Pages": results["corpus"]["pages"],
            "Cases": results["corpus"]["cases"], "Courts identified": len(results["corpus"]["courts"]),
            "Status ok": results["review"]["ok"], "Status needs review": results["review"]["needs_review"]}
    with stage("5 workbook", timings):
        report.write_xlsx(records, flat, os.path.join(output_dir, "case_index.xlsx"))
    results["stage_seconds"] = {k: round(v, 3) for k, v in timings.items()}
    results["run_seconds"] = round(time.perf_counter() - t_start, 3)
    results["throughput"] = {"documents_per_second": round(len(records) / results["run_seconds"], 2),
                             "pages_per_second": round(results["corpus"]["pages"] / results["run_seconds"], 2)}
    with open(os.path.join(output_dir, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, sort_keys=False)
        fh.write("\n")
    with open(os.path.join(output_dir, "records.json"), "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)
        fh.write("\n")
    return results
