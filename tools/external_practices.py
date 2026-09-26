#!/usr/bin/env python3
"""Pinned, opt-in upstream tools with private practice-feedback/v1 receipts.

No host/global configuration is changed. Code extraction is local only. The
upstream implementations remain upstream; this module owns routing and receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from practice_feedback import analyze, load_record

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "configs/external-practices.json"


def write_json(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            result.update(chunk)
    return result.hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE, timeout=30)


def fingerprint(repo, scope, cache):
    """Conservative working-tree identity, including untracked nonignored inputs.

    This is NOT a parser coverage count. Ignored inputs are outside this contract.
    """
    names = set(git(repo, "ls-files", "-c", "-o", "--exclude-standard", "-z", "--", scope).split(b"\0"))
    result = hashlib.sha256()
    count = 0
    for raw in sorted(names - {b""}):
        path = repo / os.fsdecode(raw)
        resolved = path.resolve()
        if resolved.is_relative_to(cache) or ".git" in path.relative_to(repo).parts:
            continue
        if path.is_symlink():
            raise ValueError("symlink source is outside the audited extraction contract: " + os.fsdecode(raw))
        if path.is_dir():
            raise ValueError("submodule/directory entry needs its own extraction scope")
        content = digest(path) if path.is_file() else "deleted"
        result.update(raw + b"\0" + content.encode() + b"\0")
        count += 1
    return {"sha256": result.hexdigest(), "candidate_files": count, "scope": scope}


def command(argv, cwd, bundle, env, timeout, executions):
    """Keep full output off model context; retain failed and timed-out attempts."""
    log = bundle / ("command-%02d.log" % len(executions))
    item = {"argv": [str(a) for a in argv], "log": log.name, "exit_code": None}
    executions.append(item)
    start = time.monotonic()
    with log.open("xb") as stream:
        process = subprocess.Popen(item["argv"], cwd=cwd, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
        try:
            item["exit_code"] = process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=stream, stderr=stream, check=False)
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait()
            item["exit_code"] = 124
    item.update(wall_seconds=time.monotonic() - start, output_bytes=log.stat().st_size)
    if item["exit_code"]:
        raise RuntimeError("command failed (%s); inspect %s" % (item["exit_code"], log))


def checkout(cache, name, pin):
    return cache / "upstream" / (name + "-" + pin["revision"])


def verified_source(source, pin):
    if git(source, "rev-parse", "HEAD").decode().strip() != pin["revision"]:
        raise ValueError("upstream revision mismatch; do not reset an existing checkout")
    if git(source, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("upstream tracked files are dirty")


def interpreter(source):
    return source / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def setup(name, pin, source, run):
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        # Interrupted downloads must not poison the canonical installation path.
        with tempfile.TemporaryDirectory(prefix="prepare-", dir=source.parent) as temp:
            pending = Path(temp) / "source"
            run(["git", "init", "-q", str(pending)])
            run(["git", "-C", str(pending), "fetch", "--depth=1", pin["repository"], pin["revision"]])
            run(["git", "-C", str(pending), "checkout", "--detach", "FETCH_HEAD"])
            verified_source(pending, pin)
            pending.rename(source)
    verified_source(source, pin)
    if name == "graphify":
        if sys.version_info < (3, 10):
            raise ValueError("Graphify needs Python 3.10+; core make check still supports 3.9+")
        if not interpreter(source).exists():
            run([sys.executable, "-m", "venv", str(source / ".venv")])
        # Editable install binds execution to the checked source, not an unrelated PATH binary.
        if not (source / ".installed.json").exists():
            run([str(interpreter(source)), "-m", "pip", "install", "-e", str(source)])
            run([str(interpreter(source)), "-m", "pip", "freeze"])
            write_json(source / ".installed.json", pin)


def graphify(args, pin, source, cache, bundle, env, run, usage):
    verified_source(source, pin)
    if not interpreter(source).is_file() or not (source / ".installed.json").is_file():
        raise ValueError("run setup graphify first; no automatic installation during a task")
    if load_record(source / ".installed.json") != pin:
        raise ValueError("installation pin changed; use a separate reviewed installation")
    scope = (args.repo / args.scope).resolve()
    if not scope.is_relative_to(args.repo) or not scope.is_dir():
        raise ValueError("scope must be an existing directory within --repo")
    scope_name = scope.relative_to(args.repo).as_posix()
    before = fingerprint(args.repo, scope_name, cache)
    usage["inputs"] = before
    key = hashlib.sha256((str(args.repo) + "\0" + scope_name).encode()).hexdigest()
    index_dir = cache / "graphs"
    index_dir.mkdir(exist_ok=True)
    state_path = index_dir / (key + ".json")
    state = load_record(state_path) if state_path.exists() else None
    fresh = bool(state and state["inputs"] == before and state["revision"] == pin["revision"])
    if fresh:
        saved = (cache / state["graph"]).resolve()
        if not saved.is_relative_to(cache):
            raise ValueError("graph reference escapes private cache")
        fresh = saved.is_file() and digest(saved) == state["graph_sha256"]
    if args.action == "build" and fresh:
        usage.update(cache_hit=True, graph=state["graph"], graph_sha256=state["graph_sha256"])
        return
    if args.action != "build" and not fresh:
        raise ValueError("graph missing, changed or stale; run build for this scope before querying")
    env = dict(env, GRAPHIFY_OUT=str(bundle / "graph"), GRAPHIFY_QUERY_LOG_DISABLE="1")
    # No provider keys, native agent CLI fallback, install hooks, remote sources or optional services.
    argv = [str(interpreter(source)), "-m", "graphify"]
    if args.action == "build":
        run(argv + ["extract", str(scope), "--code-only"], env)
        saved = bundle / "graph" / "graph.json"
        data = load_record(saved) if saved.stat().st_size <= 1024 * 1024 else None
        if data is not None and not data.get("nodes"):
            raise ValueError("extraction returned no nodes; not a usable relationship index")
    else:
        if not args.query or any(value.startswith("-") for value in args.query):
            raise ValueError("query arguments must be positional text, not upstream flags")
        if len(args.query) != (2 if args.action == "path" else 1):
            raise ValueError("query/explain require one argument; path requires two")
        run(argv + [args.action] + args.query + ["--graph", str(saved)], env)
    if fingerprint(args.repo, scope_name, cache) != before:
        raise ValueError("source changed during operation; result is not fresh")
    if args.action != "build" and digest(saved) != state["graph_sha256"]:
        raise ValueError("graph changed during query; result is not verified")
    usage.update(graph=str(saved.relative_to(cache)), graph_sha256=digest(saved))
    if args.action == "build":
        state = {"inputs": before, "revision": pin["revision"],
                 "graph": usage["graph"], "graph_sha256": usage["graph_sha256"]}
        pending = state_path.with_suffix("." + uuid.uuid4().hex + ".tmp")
        write_json(pending, state)
        os.replace(pending, state_path)


def execute(args):
    pins = load_record(LOCK)
    pin = pins[args.tool]
    cache = args.cache
    source = checkout(cache, args.tool, pin)
    bundle = cache / "runs" / uuid.uuid4().hex
    bundle.mkdir(parents=True)
    start = time.monotonic()
    executions, error, emitted = [], None, None
    usage = {"tool": args.tool, "operation": args.action, "task": args.task,
             "repo": str(args.repo), "scope": args.scope, "cache_hit": False,
             "effect": "unknown", "executions": executions,
             "native_run": os.environ.get("AGENT_RUN_ARTIFACTS"),
             "integration_sha256": digest(Path(__file__)), "lock_sha256": digest(LOCK)}
    env = os.environ.copy()
    # Do not leak configured model-provider credentials into code-only extraction.
    if args.tool == "graphify" and args.action != "setup":
        for key in list(env):
            if any(s in key for s in ("API_KEY", "ACCESS_TOKEN", "SECRET", "AUTH_TOKEN")) or key in {"PYTHONPATH", "PYTHONHOME"}:
                env.pop(key)
    def run(argv, child_env=None):
        return command(argv, args.repo, bundle, child_env or env, args.timeout, executions)
    stage = "selected"
    try:
        usage["source"] = git(args.repo, "rev-parse", "HEAD").decode().strip()
        if args.action == "skip":
            stage = "not_used"
        elif args.action == "setup":
            setup(args.tool, pin, source, run)
        elif args.tool == "ponytail":
            verified_source(source, pin)
            skill = source / pin["skill"]
            emitted = skill.read_text(encoding="utf-8")
            (bundle / "upstream-skill.md").write_bytes(skill.read_bytes())
            usage["skill"] = pin["skill"]
            stage = "loaded"
        else:
            graphify(args, pin, source, cache, bundle, env, run, usage)
            stage = "applied"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        error = str(exc)
        usage["error"] = error
    usage.update(wall_seconds=time.monotonic() - start,
                 output_bytes=sum(item.get("output_bytes", 0) for item in executions))
    write_json(bundle / "execution.json", usage)
    refs = [{"path": str(path.relative_to(cache)), "sha256": digest(path)}
            for path in sorted(bundle.iterdir()) if path.is_file()]
    receipt = {"schema": "practice-feedback/v1", "record_kind": args.kind,
               "run_id": bundle.name, "source": usage.get("source", "unresolved"),
               "task_class": args.task,
               "practices": [{"id": args.tool, "revision": pin["revision"], "stage": stage,
                              "basis": "tool_trace", "trigger": args.why,
                              "decision": args.action + " via pinned upstream", "evidence": refs}],
               "outcome": {"status": "blocked" if error else "unverified", "evidence": refs},
               "measurements": {"wall_seconds": usage["wall_seconds"], "tokens": None,
                                "instruction_bytes": len(emitted.encode()) if emitted else None}}
    analyze(receipt, cache)
    write_json(bundle / "practice-feedback.json", receipt)
    print(json.dumps({"run_id": bundle.name, "state": "BLOCKED" if error else "EXECUTED",
                      "receipt": str(bundle / "practice-feedback.json"), "error": error}))
    if emitted:
        print(emitted)
    return 2 if error else 0


def assess(args):
    bundle = (args.cache / "runs" / args.run).resolve()
    if bundle.parent != (args.cache / "runs").resolve():
        raise ValueError("invalid run ID")
    receipt = load_record(bundle / "practice-feedback.json")
    if receipt["outcome"]["status"] == "blocked" and args.status == "accepted":
        raise ValueError("a blocked attempt cannot be accepted; retain it and run a new attempt")
    if (bundle / "assessment.json").exists():
        raise ValueError("assessment already exists; preserve it, do not overwrite")
    if not args.effect.strip():
        raise ValueError("a concrete effect or explicit unknown is required")
    if args.status in {"accepted", "rejected"} and not args.evidence:
        raise ValueError("accepted/rejected requires substantive evidence, not a tool exit code")
    paths = [(args.repo / value).resolve() for value in args.evidence]
    if any(not path.is_relative_to(args.repo) or not path.is_file() for path in paths):
        raise ValueError("assessment evidence must be files within --repo")
    refs = []
    for i, path in enumerate(paths):
        target = bundle / ("assessment-evidence-%02d" % i)
        with target.open("xb") as output, path.open("rb") as source:
            import shutil
            shutil.copyfileobj(source, output)
        refs.append({"path": str(target.relative_to(args.cache)), "sha256": digest(target)})
    write_json(bundle / "assessment.json", {"status": args.status, "effect": args.effect,
               "basis": "self_report", "evidence": refs, "baseline": args.baseline})
    print("Recorded assessment; effect attribution is self_report, not causal proof.")
    return 0


def report(args):
    rows = []
    locations = {args.cache} | {Path(p).resolve() for p in getattr(args, "include_cache", [])}
    receipts = [(cache, path) for cache in sorted(locations)
                for path in sorted((cache / "runs").glob("*/practice-feedback.json"))]
    for cache, path in receipts:
        raw = load_record(path)
        result = analyze(raw, cache)
        usage = load_record(path.parent / "execution.json")
        assessment = path.parent / "assessment.json"
        effect = load_record(assessment) if assessment.exists() else None
        if effect:
            from practice_feedback import references
            evidence, resolved = references(effect["evidence"], cache)
            effect = dict(effect, evidence=evidence, evidence_resolved=resolved)
        rows.append({"run": path.parent.name, "task": usage["task"], "kind": raw["record_kind"],
                     "tool": usage["tool"], "operation": usage["operation"],
                     "revision": raw["practices"][0]["revision"], "repo": usage["repo"],
                     "scope": usage["scope"], "source": raw["source"],
                     "why": raw["practices"][0]["trigger"], "stage": raw["practices"][0]["stage"],
                     "calls": len(usage["executions"]), "wall_seconds": usage["wall_seconds"],
                     "instruction_bytes": raw["measurements"].get("instruction_bytes"),
                     "output_bytes": usage["output_bytes"], "cache_hit": usage["cache_hit"],
                     "status": result["outcome_reported"], "assessment": effect,
                     "evidence_resolved": result["practices"][0]["evidence_resolved"],
                     "receipt": str(path)})
    totals = {}
    for row in rows:
        key = row["tool"] + "/" + row["operation"] + "/" + row["kind"]
        group = totals.setdefault(key, {"records": 0, "calls": 0, "wall_seconds": 0,
                                       "output_bytes": 0, "cache_hits": 0,
                                       "instruction_bytes_known": 0, "instruction_bytes": 0})
        for field in ("calls", "wall_seconds", "output_bytes"):
            group[field] += row[field]
        group["records"] += 1
        group["cache_hits"] += int(row["cache_hit"])
        if row["instruction_bytes"] is not None:
            group["instruction_bytes_known"] += 1
            group["instruction_bytes"] += row["instruction_bytes"]
    if args.json:
        print(json.dumps({"rows": rows, "totals": totals, "coverage": "instrumented operations only; absence is not zero use",
                          "effect": "reported observations; causal savings require a matched comparison"}, indent=2))
    else:
        print("# External practice usage\n\nInstrumented operations only; not ecosystem-wide surveillance.\n")
        print("| Tool / operation / kind | Records | Calls | Seconds | Retained bytes | Skill bytes (known/records) | Cache hits |")
        print("| --- | ---: | ---: | ---: | ---: | --- | ---: |")
        def cell(value):
            return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
        for key, group in sorted(totals.items()):
            known = group["instruction_bytes_known"]
            skill_bytes = "%s (%d/%d)" % (group["instruction_bytes"] if known else "unknown", known, group["records"])
            print("| %s | %d | %d | %.3f | %d | %s | %d |" % (
                cell(key), group["records"], group["calls"], group["wall_seconds"],
                group["output_bytes"], skill_bytes, group["cache_hits"]))
        pending = sum(row["assessment"] is None for row in rows)
        blocked = sum(row["status"] == "blocked" for row in rows)
        unresolved = sum(not row["evidence_resolved"] for row in rows)
        print("\nAssessment pending: %d/%d. Blocked attempts: %d. Unresolved evidence: %d." % (
            pending, len(rows), blocked, unresolved))
        print("Use report --details for where/why/effect/evidence, or --json for all records.")
        for row in rows if getattr(args, "details", False) else []:
            print("\n## " + row["run"] + "\n")
            print("Where: `%s`, `%s`, source `%s`; upstream `%s`." % (
                cell(row["repo"]), cell(row["scope"]), row["source"], row["revision"]))
            print("Why: " + cell(row["why"]))
            print("Effect (self-reported): " + cell(row["assessment"]["effect"] if row["assessment"] else "unknown; assessment pending"))
            if row["assessment"]:
                print("Assessment evidence resolved: %s; comparison record: %s." % (
                    row["assessment"]["evidence_resolved"], cell(row["assessment"].get("baseline") or "none")))
            print("Evidence resolved: %s. Receipt: `%s`." % (row["evidence_resolved"], cell(row["receipt"])))
        if not rows:
            print("No instrumented records found. This does not establish zero usage.")
        print("\nTokens/cost and causal savings are unknown unless supplied by a matched native benchmark.\n"
              "Setup, fixtures and unsuccessful attempts remain visible; do not count them as successful development.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--cache", type=Path)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("setup", "skip", "load", "build", "query", "path", "explain"):
        p = sub.add_parser(action)
        if action in {"setup", "skip"}:
            p.add_argument("tool", choices=("ponytail", "graphify"))
        else:
            p.set_defaults(tool="ponytail" if action == "load" else "graphify")
        p.add_argument("--task", required=True, help="existing task/run identity, not a new project tracker")
        p.add_argument("--why", required=True)
        p.add_argument("--scope", default=".")
        p.add_argument("--kind", choices=("agent_run", "manual_review", "fixture"), default="agent_run")
        p.add_argument("--timeout", type=float, default=120)
        if action in ("query", "path", "explain"):
            p.add_argument("query", nargs="+")
    p = sub.add_parser("assess")
    p.add_argument("run")
    p.add_argument("--status", choices=("accepted", "rejected", "unverified"), required=True)
    p.add_argument("--effect", required=True)
    p.add_argument("--evidence", action="append", default=[])
    p.add_argument("--baseline", help="existing native matched-comparison record; no causal inference is made")
    p = sub.add_parser("report")
    p.add_argument("--json", action="store_true")
    p.add_argument("--details", action="store_true")
    p.add_argument("--include-cache", type=Path, action="append", default=[],
                   help="additional explicitly authorized private cache; no workspace discovery")
    args = parser.parse_args()
    args.repo = args.repo.resolve()
    args.cache = (args.cache or args.repo / ".agent-cache" / "external-practices").resolve()
    try:
        if args.action == "report":
            return report(args)
        if args.action == "assess":
            return assess(args)
        if not args.task.strip() or not args.why.strip() or not 0 < args.timeout <= 1800:
            raise ValueError("nonempty task/reason and timeout in (0, 1800] required")
        return execute(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"state": "INVALID", "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
