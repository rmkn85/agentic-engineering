"""Read the payload currently visible to the consumer."""
import json
from pathlib import Path

from .identity import digest


_responses = {}


def read_current(workspace):
    workspace = Path(workspace)
    manifest = json.loads((workspace / "current.json").read_text(encoding="utf-8"))
    key = (str(workspace.resolve()), manifest["version"])
    if key in _responses:
        return _responses[key]
    payload = (workspace / "installed" / manifest["sha256"] / "payload.txt").read_bytes()
    response = {"version": manifest["version"], "sha256": digest(payload),
                "text": payload.decode("utf-8")}
    _responses[key] = response
    return response
