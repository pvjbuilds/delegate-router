import json
from pathlib import Path
import sys

answer = Path(sys.argv[1]) / "answer.json"
assert answer.is_file(), "answer.json missing"
data = json.loads(answer.read_text())
assert isinstance(data, dict) and set(data) == {"total", "cancelled", "top_region", "bottom_region"}, "wrong keys"
assert isinstance(data["total"], str) and data["total"].strip() == "209.65", "wrong total"
assert data["cancelled"] == ["C-019", "F-077"], "wrong cancelled rows"
assert data["top_region"] == "East", "wrong top region"
assert data["bottom_region"] == "West", "wrong bottom region"
