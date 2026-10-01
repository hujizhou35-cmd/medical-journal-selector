"""Regenerate the clearly fictional teaching example from test fixtures."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "development/tests"))
sys.path.insert(0, str(ROOT / "skills/medical-journal-selector/scripts"))
from fixtures import fixture
from selector import validate, render

b = fixture()
assert not validate(b), validate(b)
out = ROOT / "docs/examples"
out.mkdir(parents=True, exist_ok=True)
(out / "fictional-evidence.json").write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
(out / "fictional-report.md").write_text(render(b), encoding="utf-8")
print("Fictional example generated; no real journal claims.")
