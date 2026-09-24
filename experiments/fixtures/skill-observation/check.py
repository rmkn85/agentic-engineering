#!/usr/bin/env python3
"""Check a pilot answer against the retained raw log."""

import hashlib
import json
from pathlib import Path
import sys


root = Path(sys.argv[1])
answer = json.loads((root / "answer.json").read_text())
manifests = list((root / "logs").glob("*/manifest.json"))
if len(manifests) != 1:
    raise SystemExit("expected one quiet-run bundle")
manifest = json.loads(manifests[0].read_text())
raw = (manifests[0].parent / "full.log").read_bytes()
digest = hashlib.sha256(raw).hexdigest()
if manifest["status"] != "PASS" or manifest["evidence"][0]["sha256"] != digest:
    raise SystemExit("quiet-run receipt does not match raw log")
if answer["sha256"] != digest:
    raise SystemExit("answer hash does not match raw log")
found = []
for line_number, line in enumerate(raw.decode().splitlines(), 1):
    if line.startswith("ASSERTION "):
        found.append({"line": line_number, "text": line})
if answer["failures"] != found:
    raise SystemExit("failure list or exact text differs")
print(json.dumps({"accepted": True, "failures": len(found), "raw_bytes": len(raw), "sha256": digest}))
