#!/usr/bin/env python3
"""Explicit offline preflight/record for native documentation-tool responses."""
import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time
import uuid

WIDE_FAILURES = {"quota", "auth", "spend", "outage"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("symlink input or cache file")
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps require a timezone")
    return parsed.timestamp()


def request(path):
    value = load(path)
    if set(value) != {"provider", "operation", "arguments", "namespace", "source"}:
        raise ValueError("request requires exactly provider, operation, arguments, namespace, source")
    for key in ("provider", "operation", "namespace", "source"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(key + " must be a nonempty string")
    if not isinstance(value["arguments"], dict):
        raise ValueError("arguments must be an object")
    canonical(value)
    return value


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def gate_lock(path):
    """Serialize short gate updates; an abandoned lock requires inspection."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = path.with_suffix(".lock")
    deadline = time.monotonic() + 5
    while True:
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise ValueError("gate mutation locked; inspect owner before retrying")
            time.sleep(0.01)
    try:
        yield
    finally:
        lock.unlink()


def gate_references(state):
    if "record" in state:  # compatibility with a previously recorded gate
        return [state["record"]]
    if "records" in state and isinstance(state["records"], list):
        return state["records"]
    if state.get("evidence") and "released_at" in state:
        return []
    raise ValueError("invalid failure state")


def record_read(root, reference):
    # References are generated basenames; never follow a record-supplied path.
    if not isinstance(reference, str) or Path(reference).name != reference:
        raise ValueError("invalid record reference")
    path = root / "records" / reference
    if path.is_symlink():
        raise ValueError("symlink record")
    envelope = load(path)
    body = envelope["body"]
    if digest(body) != envelope["sha256"]:
        raise ValueError("record hash mismatch")
    return body, str(path), envelope["sha256"]


def run(args, now=None):
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    root = Path(args.cache_dir)
    for directory in (root, root / "records", root / "entries", root / "gates"):
        if directory.is_symlink():
            raise ValueError("cache directories must not be symlinks")
    req = request(args.request)
    key = digest(req)
    scope = digest({"provider": req["provider"], "namespace": req["namespace"]})
    entry = root / "entries" / (key + ".json")
    gate = root / "gates" / (scope + ".json")
    if args.command == "record":
        response = load(args.response)
        kind = args.kind
        if kind == "success":
            if args.valid_for is None or not math.isfinite(args.valid_for) or args.valid_for <= 0:
                raise ValueError("success requires positive finite --valid-for")
            if isinstance(response, dict) and (response.get("isError") or "error" in response):
                raise ValueError("an error response cannot be documentation")
        retry = timestamp(args.retry_at) if args.retry_at else None
        if retry is not None and retry <= now:
            raise ValueError("retry boundary must be in the future when recorded")
        body = {"request": req, "kind": kind, "recorded_at": now,
                "expires_at": now + args.valid_for if kind == "success" else None,
                "retry_at": retry, "response": response}
        reference = uuid.uuid4().hex + ".json"
        atomic(root / "records" / reference, {"body": body, "sha256": digest(body)})
        if kind in WIDE_FAILURES:
            with gate_lock(gate):
                previous = load(gate) if gate.exists() else {"records": []}
                atomic(gate, {"records": gate_references(previous) + [reference], "previous_release": previous.get("evidence")})
        else:
            atomic(entry, {"record": reference})
        return {"status": "recorded", "kind": kind, "record": str(root / "records" / reference), "sha256": digest(body)}
    if args.command == "release":
        if not args.evidence.strip():
            raise ValueError("release requires meaningful changed-condition evidence")
        # Preserve the inspected failure reference; release is not documentation.
        with gate_lock(gate):
            previous = load(gate)
            atomic(gate, {"records": [], "released_at": now, "evidence": args.evidence, "previous": previous})
        return {"status": "released", "evidence": args.evidence}
    if not math.isfinite(args.max_age) or args.max_age < 0:
        raise ValueError("--max-age must be finite and nonnegative")
    # A provider failure prevents new probes, not reuse of already valid docs.
    result = {"status": "miss", "reason": "missing or invalid record"}
    try:
        body, path, sha = record_read(root, load(entry)["record"])
        if body["request"] != req:
            raise ValueError("request identity mismatch")
        if body["kind"] != "success":
            result = {"status": "miss", "reason": "request failure", "record": path}
        else:
            age = now - body["recorded_at"]
            if age < 0 or age > args.max_age or now >= body["expires_at"]:
                result = {"status": "miss", "reason": "expired or outside caller freshness"}
            else:
                return {"status": "hit", "record": path, "sha256": sha, "recorded_at": body["recorded_at"], "expires_at": body["expires_at"], "response": body["response"]}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if gate.with_suffix(".lock").exists():
        return {"status": "blocked", "reason": "failure gate mutation pending; inspect owner if abandoned"}
    if gate.exists():
        try:
            state = load(gate)
            for reference in gate_references(state):
                body, path, sha = record_read(root, reference)
                if (body["request"]["provider"], body["request"]["namespace"]) != (req["provider"], req["namespace"]) or body["kind"] not in WIDE_FAILURES:
                    raise ValueError("gate identity mismatch")
                if body["retry_at"] is None or now < body["retry_at"]:
                    return {"status": "blocked", "reason": body["kind"], "retry_at": body["retry_at"], "record": path, "sha256": sha}
        except (OSError, ValueError, KeyError, TypeError):
            return {"status": "blocked", "reason": "invalid failure state; inspect or release with changed-condition evidence"}
    return result



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", default=".agent-cache/docs-results")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("lookup", "record", "release"):
        command = commands.add_parser(name)
        command.add_argument("--request", required=True)
        if name == "lookup":
            command.add_argument("--max-age", required=True, type=float)
        elif name == "record":
            command.add_argument("--response", required=True)
            command.add_argument("--kind", required=True, choices=["success", "request"] + sorted(WIDE_FAILURES))
            command.add_argument("--valid-for", type=float)
            command.add_argument("--retry-at")
        else:
            command.add_argument("--evidence", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args), ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, "docs cache: " + str(error) + "\n")


if __name__ == "__main__":
    main()
