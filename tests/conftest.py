import json
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CORPUS = ROOT / "data" / "corpus"


@pytest.fixture(scope="session")
def corpus_dir():
    if not CORPUS.exists() or not list(CORPUS.glob("*.pdf")):
        pytest.skip("corpus not downloaded: run `python scripts/fetch_corpus.py` first")
    return CORPUS


@pytest.fixture(scope="session")
def run_output(corpus_dir, tmp_path_factory):
    from courtfile.pipeline import run
    out = tmp_path_factory.mktemp("run")
    results = run(str(corpus_dir), str(out), str(ROOT / "reference"))
    records = json.loads((out / "records.json").read_text())
    return results, records, out
