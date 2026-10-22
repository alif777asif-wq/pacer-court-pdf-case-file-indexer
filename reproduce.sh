#!/usr/bin/env bash
# One command reproduces the whole run: bash reproduce.sh
# System tools required: python3 (3.10+) with venv, poppler-utils (pdftotext), tesseract-ocr.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --quiet --requirement requirements.txt
mkdir -p proof
python scripts/fetch_corpus.py 2>&1 | tee proof/fetch.log
rm -rf proof/outputs
PYTHONPATH=src python -m courtfile run --input data/corpus --output proof/outputs --reference reference --log proof/run.log
find proof/outputs/case_files -type f | sort | sed 's#^proof/outputs/##' > proof/outputs/case_files.tree.txt
# the sed only replaces this checkout's absolute path with "." so the log carries no machine-specific paths
PYTHONPATH=src python -m pytest -v --no-header --junitxml=proof/pytest-junit.xml tests 2>&1 | sed "s#$PWD#.#g" | tee proof/pytest.txt
python scripts/summarise_tests.py proof/pytest-junit.xml
python scripts/record_env.py proof/env.json > /dev/null
echo "reproduction complete: see proof/results.json (proof/outputs/results.json)"
