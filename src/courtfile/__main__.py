"""Command line: python -m courtfile run --input DIR --output DIR [--reference DIR] [--log FILE] [--no-ocr]"""
import argparse
import logging
import sys

from .pipeline import run


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="courtfile", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="identify, classify, organise and index a folder of court PDFs")
    r.add_argument("--input", required=True)
    r.add_argument("--output", required=True)
    r.add_argument("--reference", default=None, help="folder holding reference_labels.csv (optional)")
    r.add_argument("--log", default=None, help="also write the timestamped log to this file")
    r.add_argument("--no-ocr", action="store_true")
    args = ap.parse_args(argv)

    handlers = [logging.StreamHandler(sys.stdout)]
    if args.log:
        handlers.append(logging.FileHandler(args.log, mode="w", encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", handlers=handlers)
    results = run(args.input, args.output, args.reference, ocr=not args.no_ocr)
    logging.getLogger("courtfile").info("run complete: %s documents, %s needing review",
                                        results["corpus"]["documents"], results["review"]["needs_review"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
