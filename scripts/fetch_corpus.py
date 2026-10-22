"""Download the pinned input corpus and verify every file against corpus.lock.json.

Usage: python scripts/fetch_corpus.py [--dest data/corpus]
Exits non-zero if any download fails or any checksum differs from the lock file.
"""
import argparse
import hashlib
import json
import logging
import pathlib
import sys
import urllib.request

LOG = logging.getLogger("fetch_corpus")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", default="corpus.lock.json")
    ap.add_argument("--dest", default="data/corpus")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    lock = json.loads(pathlib.Path(args.lock).read_text())
    dest = pathlib.Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    failures = 0
    for entry in lock["files"]:
        target = dest / entry["local_name"]
        try:
            if not target.exists():
                with urllib.request.urlopen(entry["url"], timeout=60) as resp:
                    target.write_bytes(resp.read())
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError as exc:
            LOG.error("download failed for %s: %s", entry["local_name"], exc)
            failures += 1
            continue
        if digest != entry["sha256"]:
            LOG.error("CHECKSUM MISMATCH %s expected %s got %s", entry["local_name"], entry["sha256"], digest)
            failures += 1
        else:
            LOG.info("ok %s %s", entry["local_name"], digest[:12])
    LOG.info("fetched %d files, %d failures", len(lock["files"]), failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
