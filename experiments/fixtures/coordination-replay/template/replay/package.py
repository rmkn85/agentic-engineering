"""Build an immutable package from a selected source file."""
import json
from pathlib import Path

from .identity import digest


def build(source_file, workspace, version):
    source = Path(source_file).read_bytes()
    source_digest = digest(source)
    package_dir = Path(workspace) / "packages" / source_digest
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "payload.txt").write_bytes(source)
    manifest = {"version": version, "sha256": source_digest}
    (package_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
    )
    return package_dir, manifest
