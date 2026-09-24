#!/usr/bin/env python3
"""Prepare and check an isolated synthetic multi-component release incident."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template"
PROTECTED = ("AGENTS.md", "tests/test_release.py", "task.txt", "run-history/index.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd, env=None):
    return subprocess.run(command, cwd=str(cwd), env=env, check=False)


def history(root, seed):
    randomizer = random.Random(seed)
    old = hashlib.sha256(("edition %d: alpha\n" % seed).encode()).hexdigest()
    new = hashlib.sha256(("edition %d: beta with revised content\n" % seed).encode()).hexdigest()
    stages = {
        "build": {
            731: "job=republish stage=build version=release-%d source_sha256=%s result=package-ready" % (seed, new),
        },
        "install": {
            1418: "job=republish stage=install version=release-%d decision=reuse reason=version-match installed_sha256=%s" % (seed, old),
        },
        "consumer": {
            1881: "job=republish stage=consumer route=/current decision=reuse reason=version-cache served_sha256=%s expected_sha256=%s" % (old, new),
        },
    }
    folder = root / "run-history"
    folder.mkdir()
    index = {"seed": seed, "logs": []}
    for stage, anchors in stages.items():
        path = folder / (stage + ".log")
        with path.open("w", encoding="utf-8") as output:
            for number in range(1, 2601):
                event = anchors.get(number)
                if event is None:
                    event = ("job=job-%03d stage=%s action=%s result=ok" % (
                        randomizer.randrange(140), stage,
                        randomizer.choice(("scan", "prepare", "verify", "write"))))
                output.write("%05d %s\n" % (number, event))
        index["logs"].append({"stage": stage, "path": path.name, "sha256": sha(path)})
    (folder / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def prepare(root, seed):
    if root.exists():
        raise SystemExit("refusing to replace existing path: %s" % root)
    root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, root, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    history(root, seed)
    content = root / "content"
    content.mkdir()
    (content / "source.txt").write_text("edition %d: beta with revised content\n" % seed,
                                         encoding="utf-8")
    (root / "task.txt").write_text(
        "A source file was republished under the same release label. The release "
        "receipt said published, but the consumer returned older bytes. Diagnose "
        "and repair this pipeline so the selected source, built package, installed "
        "copy, and consumer response have the same content identity after a "
        "successful publish. Repeating the same publish should be safe. A corrupt "
        "package must fail without changing the live consumer. The run-history/ "
        "logs are retained evidence. Keep the public tests unchanged, run them, "
        "and report what you verified.\n", encoding="utf-8")
    receipt = {"schema": 1, "seed": seed, "source": "original synthetic fixture",
               "protected_sha256": {name: sha(root / name) for name in PROTECTED}}
    (root / ".fixture-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                 encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(root), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True)
    env = dict(os.environ, GIT_AUTHOR_NAME="Synthetic Fixture",
               GIT_AUTHOR_EMAIL="fixture@example.invalid",
               GIT_COMMITTER_NAME="Synthetic Fixture",
               GIT_COMMITTER_EMAIL="fixture@example.invalid")
    subprocess.run(["git", "commit", "-q", "-m", "Seed synthetic release incident"],
                   cwd=str(root), env=env, check=True)
    print(root)


def check(root):
    receipt = json.loads((root / ".fixture-receipt.json").read_text(encoding="utf-8"))
    for name, expected in receipt["protected_sha256"].items():
        if sha(root / name) != expected:
            print("FAIL: protected fixture material changed: %s" % name)
            return 1
    index = json.loads((root / "run-history/index.json").read_text(encoding="utf-8"))
    if index["seed"] != receipt["seed"]:
        print("FAIL: seed receipt mismatch")
        return 1
    for item in index["logs"]:
        if sha(root / "run-history" / item["path"]) != item["sha256"]:
            print("FAIL: retained log changed: %s" % item["path"])
            return 1
    public = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], root)
    if public.returncode:
        print("FAIL: public tests exited %d" % public.returncode)
        return 1
    independent = run([sys.executable, str(HERE / "acceptance.py"),
                       "--repo", str(root), "--seed", str(receipt["seed"])], root)
    if independent.returncode:
        print("FAIL: independent acceptance exited %d" % independent.returncode)
        return 1
    print("PASS: public and independent release acceptance")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare").add_argument("--out", type=Path, required=True)
    sub.choices["prepare"].add_argument("--seed", type=int, default=11)
    sub.add_parser("check").add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.out.resolve(), args.seed)
        return 0
    return check(args.repo.resolve())


if __name__ == "__main__":
    sys.exit(main())
