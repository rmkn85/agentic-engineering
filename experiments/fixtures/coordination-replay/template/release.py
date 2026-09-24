"""Publish a source file through the package, install, and consumer stages."""
import argparse
import json
from pathlib import Path

from replay.consumer import read_current
from replay.identity import digest
from replay.install import install
from replay.package import build


def publish(source_file, workspace, version):
    source_sha = digest(Path(source_file).read_bytes())
    package_dir, package_manifest = build(source_file, workspace, version)
    installed_manifest = install(package_dir, workspace)
    served = read_current(workspace)
    return {
        "status": "published",
        "version": version,
        "source_sha256": source_sha,
        "package_sha256": package_manifest["sha256"],
        "installed_sha256": installed_manifest["sha256"],
        "served_sha256": served["sha256"],
        "served_text": served["text"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_file")
    parser.add_argument("workspace")
    parser.add_argument("version")
    args = parser.parse_args()
    print(json.dumps(publish(args.source_file, args.workspace, args.version), sort_keys=True))
