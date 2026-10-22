"""Turn pytest's JUnit XML into proof/test-summary.json (counts and duration)."""
import json
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1] if len(sys.argv) > 1 else "proof/pytest-junit.xml").getroot()
suite = root if root.tag == "testsuite" else root.find("testsuite")
summary = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
summary["passed"] = summary["tests"] - summary["failures"] - summary["errors"] - summary["skipped"]
summary["seconds"] = float(suite.get("time", 0))
json.dump(summary, open("proof/test-summary.json", "w"), indent=2)
print(json.dumps(summary))
