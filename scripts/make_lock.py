"""Developer script: pin the input corpus (source URL @ commit, sha256, size) into corpus.lock.json.

Run once from a machine that has local checkouts of the two source repositories.
Candidates that fail the documented screening rules are recorded under "excluded" with the reason.
"""
import datetime
import hashlib
import json
import pathlib
import sys

DOCTOR = ("freelawproject/doctor", "cce98c25f5bcf4b7340b33c5d81cfb2466624b4e")
XRAY = ("freelawproject/x-ray", "4dd5b0bcc5cdd774b9e82fc47b1d7208e92e4779")

SRC = {}  # local_name -> (repo, commit, path-in-repo)
for n in ["ca10_010110462922", "ca1_00117684624", "ca2_1-1", "ca7_3"]:
    SRC[f"doctor__{n}.pdf"] = (*DOCTOR, f"doctor/test_assets/recap_documents/{n}.pdf")
for n in ["gov.uscourts.azd.1085839.3.0", "gov.uscourts.cacd.652774.40.0", "gov.uscourts.cand.203070.27.0"]:
    SRC[f"doctor__{n}.pdf"] = (*DOCTOR, f"doctor/test_assets/recap_extract/{n}.pdf")
for n in ["multi_line_redaction_ok", "no_bad_redactions.4.1", "no_bad_redactions.6.2",
          "rect_ordering_0.8", "rect_ordering_4.1", "rectangles_no"]:
    SRC[f"xray__{n}.pdf"] = (*XRAY, f"tests/assets/{n}.pdf")

EXCLUDED = {
    "pii-screen: contact details (email/phone/street address) detected": [
        "doctor/recap_documents/ca3_003112692106", "doctor/recap_documents/ca4_17 (found only after OCR)",
        "doctor/recap_documents/ca6_1-3", "doctor/recap_documents/ca8_",
        "doctor/recap_documents/ca9_19", "doctor/recap_documents/cafc_3",
        "x-ray/no_bad_redactions.2.1", "x-ray/no_bad_redactions.3.2", "x-ray/ok_words",
        "x-ray/partial_intersections_ok", "x-ray/rect_ordering_1.23", "x-ray/rect_ordering_3.20",
        "x-ray/rect_ordering_6.19", "x-ray/unfilled_rect", "x-ray/hidden_text_on_visible_text"],
    "redaction test file whose name states that redacted text is recoverable": [
        "x-ray/bad_cross_hatched_redactions", "x-ray/rectangles_yes",
        "x-ray/whitespace_redaction_with_comma", "x-ray/whitespace_redactions",
        "x-ray/whitespace_redactions_2"],
    "not a court filing (map printout / letter-sequence test file)": [
        "x-ray/no_bad_redactions.3.1", "x-ray/rectangles_yes_2"],
    "personal financial records of an individual debtor": ["x-ray/rect_ordering_2.1", "x-ray/rect_ordering_5.2"],
    "sensitive personal matter (immigration removal, habeas judgment, detention-case exhibit, "
    "insured spouse's death benefit, individual declarant's residence)": [
        "doctor/ca1-opinion", "doctor/recap_documents/ca5_00516242060", "x-ray/no_bad_redactions.7.1",
        "x-ray/no_bad_redactions.8.1", "x-ray/no_bad_redactions.5.5"],
}


def main(root: str) -> None:
    root_path = pathlib.Path(root)
    files = []
    for local, (repo, sha, path) in SRC.items():
        data = (root_path / repo.split("/")[1] / path).read_bytes()
        files.append({
            "local_name": local,
            "source_repo": f"https://github.com/{repo}",
            "commit": sha,
            "path_in_repo": path,
            "url": f"https://raw.githubusercontent.com/{repo}/{sha}/{path}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })
    lock = {
        "retrieved": datetime.date.today().isoformat(),
        "licence": "BSD-2-Clause (repository licence of freelawproject/doctor and freelawproject/x-ray)",
        "note": "Public federal-court records distributed as open test assets by Free Law Project.",
        "files": files,
        "excluded": [{"candidate": c, "reason": r} for r, cs in EXCLUDED.items() for c in cs],
    }
    pathlib.Path("corpus.lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    print(len(files), "files pinned;", len(lock["excluded"]), "candidates excluded")


if __name__ == "__main__":
    main(sys.argv[1])
