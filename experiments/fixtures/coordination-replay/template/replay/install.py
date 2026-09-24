"""Install a verified package and point the consumer to it."""
import json
import os
from pathlib import Path
import shutil

from .identity import digest


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def install(package_dir, workspace):
    package_dir = Path(package_dir)
    workspace = Path(workspace)
    manifest = _read_json(package_dir / "manifest.json")
    pointer = workspace / "current.json"
    if pointer.exists():
        current = _read_json(pointer)
        # A version can be republished with different source bytes.
        if current["version"] == manifest["version"]:
            return current

    payload = (package_dir / "payload.txt").read_bytes()
    if digest(payload) != manifest["sha256"]:
        raise ValueError("package payload does not match manifest")
    installed = workspace / "installed" / manifest["sha256"]
    installed.parent.mkdir(parents=True, exist_ok=True)
    if not installed.exists():
        staged = installed.with_name(installed.name + ".staged")
        if staged.exists():
            shutil.rmtree(staged)
        staged.mkdir()
        (staged / "payload.txt").write_bytes(payload)
        (staged / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(staged, installed)
    else:
        if digest((installed / "payload.txt").read_bytes()) != manifest["sha256"]:
            raise ValueError("installed payload does not match manifest")
    temporary = pointer.with_suffix(".new")
    temporary.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, pointer)
    return manifest
