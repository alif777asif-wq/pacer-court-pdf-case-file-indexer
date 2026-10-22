"""Write proof/env.json: tool names, exact versions and the date/time of the run."""
import datetime
import importlib.metadata as md
import json
import platform
import subprocess
import sys


def cmd(*args):
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=20)
        return (out.stdout + out.stderr).strip().splitlines()[0]
    except Exception as exc:  # tool missing
        return f"unavailable: {exc}"


packages = ["pdfminer.six", "pypdfium2", "pytesseract", "pillow", "openpyxl", "pytest", "playwright"]
versions = {}
for name in packages:
    try:
        versions[name] = md.version(name)
    except md.PackageNotFoundError:
        versions[name] = "not installed"
env = {
    "recorded_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "poppler_pdftotext": cmd("pdftotext", "-v"),
    "tesseract": cmd("tesseract", "--version"),
    "packages": versions,
}
json.dump(env, open(sys.argv[1] if len(sys.argv) > 1 else "proof/env.json", "w"), indent=2)
print(json.dumps(env, indent=2))
