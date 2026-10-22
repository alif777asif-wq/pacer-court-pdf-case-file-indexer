"""Filename hints, collision-free target paths and verified copying into a court/case folder tree."""
from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil

LOG = logging.getLogger("courtfile.organize")

_RECAP = re.compile(r"^gov\.uscourts\.(?P<court>[a-z0-9]+)\.(?P<docket>[\w-]+?)\.(?P<doc>\d+)\.(?P<att>\d+)$")
_CIRCUIT = re.compile(r"^(?P<court>ca(?:\d{1,2}|dc|fc))_(?P<doc>[\w-]*)$")


def filename_hints(filename: str) -> dict:
    """Court id and document number encoded in RECAP-style file names (for example ``ca10_0101104...``)."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    stem = re.sub(r"^[a-z]+__", "", stem)          # strip a source prefix such as "doctor__"
    m = _RECAP.match(stem)
    if m:
        return {"court": m["court"], "doc_number": m["doc"]}
    m = _CIRCUIT.match(stem)
    if m:
        return {"court": m["court"], "doc_number": m["doc"] or None}
    return {}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def target_path(rec: dict) -> str:
    court = rec.get("court") or "_court-unresolved"
    case = (rec.get("case_number") or "_case-unresolved").replace(":", "-")
    parts = [rec.get("doc_number") or "nodoc", slug(rec["doc_type"])]
    if rec.get("filed"):
        parts.insert(1, rec["filed"])
    if rec.get("stamp_total") and rec.get("stamp_page") and rec["is_complete"] is False:
        parts.append(f"p{rec['stamp_page']}-of-{rec['stamp_total']}")
    return os.path.join(court, case, "_".join(parts) + ".pdf")


def plan_paths(records: list[dict]) -> None:
    """Assign ``new_path`` to every record; a short checksum is appended only when two records collide."""
    seen: dict[str, dict] = {}
    for rec in records:
        path = target_path(rec)
        if path in seen:
            for r in (seen[path], rec):
                r["new_path"] = path[:-4] + f"_{r['sha256'][:8]}.pdf"
        else:
            rec["new_path"] = path
            seen[path] = rec


def copy_tree(records: list[dict], src_dir: str, dest_dir: str) -> int:
    """Copy each PDF to its target path and verify the copy byte-for-byte by SHA-256."""
    copied = 0
    for rec in records:
        dst = os.path.join(dest_dir, rec["new_path"])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(src_dir, rec["filename"]), dst)
        with open(dst, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != rec["sha256"]:
                raise RuntimeError(f"copy verification failed for {dst}")
        copied += 1
    return copied
