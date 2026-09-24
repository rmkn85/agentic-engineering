#!/usr/bin/env python3
"""Ordinary short-file control task and independent checker."""

import argparse
import hashlib
import json
from pathlib import Path
import random


def rows(seed):
    rng = random.Random(seed)
    states = ["ready", "blocked", "waiting"]
    return [f"item-{number:02d} {rng.choice(states)}\n" for number in range(1, 13)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "check"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    data = "".join(rows(args.seed)).encode()
    if args.command == "setup":
        args.run_dir.mkdir(parents=True, exist_ok=True)
        (args.run_dir / "items.txt").write_bytes(data)
        (args.run_dir / "task.txt").write_text(
            'Count lines whose state is exactly "ready" in items.txt. Write answer.json '
            'as {"ready_count": <integer>}.\n', encoding="utf-8"
        )
        print(json.dumps({"run_dir": str(args.run_dir), "task": str(args.run_dir / "task.txt")}))
        return
    try:
        if (args.run_dir / "items.txt").read_bytes() != data:
            raise ValueError("items.txt differs from the seeded fixture")
        answer = json.loads((args.run_dir / "answer.json").read_text(encoding="utf-8"))
        count = sum(line.endswith(" ready\n") for line in rows(args.seed))
        if answer != {"ready_count": count}:
            raise ValueError("incorrect count")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"small case: {error}\n")
    print(json.dumps({"accepted": True, "seed": args.seed, "ready_count": count, "input_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))


if __name__ == "__main__":
    main()
