#!/usr/bin/env python3
"""Run a reproducible local Codex benchmark and capture JSONL usage.

This intentionally avoids guessing the user's model/config flags. Put the desired
model, reasoning effort, AGENTS.md, skills and Codex settings in the selected
CODEX_HOME/profile, then benchmark identical task prompts across variants.
"""
from __future__ import annotations
import argparse, json, os, shlex, statistics, subprocess, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path


def sh(cmd, cwd=None, check=True, capture=False, env=None):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None,
                          env=env)


def git(repo, *args, capture=True):
    p = sh(["git", "-C", str(repo), *args], check=True, capture=capture)
    return p.stdout.strip() if capture else ""


USAGE_FIELDS=("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")


def summarize_events(events_path):
    counts={"turns":0,"commands":0,"file_changes":0,"mcp_calls":0,"web_searches":0,"agent_messages":0,"errors":0}
    per_turn=[]
    with events_path.open(errors="replace") as f:
        for line in f:
            try: e=json.loads(line)
            except json.JSONDecodeError: continue
            typ=e.get("type","")
            if typ=="turn.completed":
                counts["turns"]+=1
                u=e.get("usage")
                per_turn.append(u if isinstance(u,dict) else {})
            elif typ=="error": counts["errors"]+=1
            if typ.startswith("item."):
                item=e.get("item") or {}
                it=item.get("type","")
                if it=="command_execution" and typ=="item.completed": counts["commands"]+=1
                elif it in {"file_change","file_changes"} and typ=="item.completed": counts["file_changes"]+=1
                elif "mcp" in it and typ=="item.completed": counts["mcp_calls"]+=1
                elif "web_search" in it and typ=="item.completed": counts["web_searches"]+=1
                elif it=="agent_message" and typ=="item.completed": counts["agent_messages"]+=1
    # A partial total would look measured. Require every completed turn to report
    # each field before publishing its aggregate.
    usage={k:sum(u[k] for u in per_turn) if per_turn and all(type(u.get(k)) is int and u[k]>=0 for u in per_turn) else None
           for k in USAGE_FIELDS}
    return usage, per_turn, counts


def summarize_root_responses(events_path, codex_home):
    """Read per-response usage for the CLI thread when its local trace exists."""
    thread_id=None
    with events_path.open(errors="replace") as events:
        for line in events:
            try: event=json.loads(line)
            except json.JSONDecodeError: continue
            if event.get("type")=="thread.started":
                thread_id=event.get("thread_id")
                break
    if not isinstance(thread_id,str) or not thread_id:
        return None
    session_root=Path(codex_home or Path.home()/".codex")/"sessions"
    paths=list(session_root.rglob(f"*-{thread_id}.jsonl")) if session_root.exists() else []
    if len(paths)!=1:
        return None
    records={}
    compactions=0
    with paths[0].open(errors="replace") as session:
        for line in session:
            try: item=json.loads(line)
            except json.JSONDecodeError: continue
            if item.get("type")=="compacted":
                compactions+=1
            if item.get("type")!="token_usage_record": continue
            payload=item.get("payload") or {}
            rid=payload.get("response_id")
            usage=payload.get("usage") or {}
            if not isinstance(rid,str) or not rid or rid in records: continue
            if all(type(usage.get(k)) is int and usage[k]>=0 for k in USAGE_FIELDS):
                records[rid]=usage
    if not records:
        return None
    inputs=[u["input_tokens"] for u in records.values()]
    cached=[u["cached_input_tokens"] for u in records.values()]
    return {"response_count":len(records),"compaction_count":compactions,
            "median_input_tokens":statistics.median(inputs),
            "peak_input_tokens":max(inputs),
            "peak_cached_input_tokens":max(cached)}


def collect_practice_feedback(run_dir):
    """Optional local sidecar; never infer usage or replace native acceptance."""
    from practice_feedback import analyze, load_record, summarize
    path = run_dir / "practice-feedback.json"
    if not path.exists():
        return {"state": "not_recorded"}
    try:
        if path.is_symlink():
            raise ValueError("feedback receipt must be a file in this run")
        result = analyze(load_record(path), run_dir)
        report = summarize([result])
        output = run_dir / "practice-summary.json"
        with output.open("x", encoding="utf-8") as stream:
            json.dump({**report, "details": [result]}, stream, indent=2, allow_nan=False)
            stream.write("\n")
        return {"state": "recorded", "summary": output.name,
                "reported_outcome": result["outcome_reported"],
                "outcome_evidence_resolved": result["outcome_evidence_resolved"],
                "practices_reported": len(result["practices"]),
                "practices_with_resolved_evidence": sum(p["evidence_resolved"] for p in result["practices"])}
    except (OSError, ValueError, TypeError, AttributeError) as error:
        return {"state": "invalid", "error": str(error)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--label", required=True)
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt")
    g.add_argument("--prompt-file")
    ap.add_argument("--codex-home")
    ap.add_argument("--profile")
    ap.add_argument("--eval-command", help="deterministic acceptance command run after Codex")
    ap.add_argument("--runs-dir", default=".agent-bench/runs")
    ap.add_argument("--keep-worktree", action="store_true")
    ap.add_argument("--codex-arg", action="append", default=[])
    ns=ap.parse_args()

    repo=Path(ns.repo).resolve()
    prompt=ns.prompt if ns.prompt is not None else Path(ns.prompt_file).read_text()
    commit=git(repo,"rev-parse",ns.base)
    ts=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir=(repo/ns.runs_dir/f"{ts}-{ns.label}").resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    wt=Path(tempfile.mkdtemp(prefix=f"codex-bench-{ns.label}-"))
    # git worktree requires target not to preexist
    wt.rmdir()
    git(repo,"worktree","add","--detach",str(wt),commit,capture=False)

    env=os.environ.copy()
    env["AGENT_RUN_ARTIFACTS"]=str(run_dir)
    if ns.codex_home:
        env["CODEX_HOME"]=str(Path(ns.codex_home).expanduser().resolve())

    cmd=["codex"]
    if ns.profile:
        cmd += ["--profile", ns.profile]
    cmd += ["exec","--json"]
    for extra in ns.codex_arg:
        cmd += shlex.split(extra)
    cmd += [prompt]

    events_path=run_dir/"events.jsonl"
    stderr_path=run_dir/"stderr.log"
    started=time.monotonic()
    with events_path.open("w") as out, stderr_path.open("w") as err:
        proc=subprocess.run(cmd,cwd=wt,env=env,text=True,stdout=out,stderr=err)
    wall=time.monotonic()-started

    usage, per_turn, counts=summarize_events(events_path)
    root_responses=summarize_root_responses(events_path,env.get("CODEX_HOME"))

    eval_code=None; eval_wall=None
    if ns.eval_command:
        t=time.monotonic()
        ep=subprocess.run(ns.eval_command,cwd=wt,env=env,shell=True,text=True,
                          stdout=(run_dir/"eval.stdout.log").open("w"),
                          stderr=(run_dir/"eval.stderr.log").open("w"))
        eval_wall=time.monotonic()-t; eval_code=ep.returncode

    diff_num=git(wt,"diff","--numstat")
    changed=git(wt,"status","--short")
    (run_dir/"diff.numstat").write_text(diff_num+"\n")
    (run_dir/"status.txt").write_text(changed+"\n")
    changed_files=sum(1 for x in changed.splitlines() if x.strip())
    ins=dels=0
    for line in diff_num.splitlines():
        parts=line.split("\t")
        if len(parts)>=2:
            if parts[0].isdigit(): ins+=int(parts[0])
            if parts[1].isdigit(): dels+=int(parts[1])

    input_t=usage["input_tokens"]
    cached_t=usage["cached_input_tokens"]
    cache_known=input_t is not None and cached_t is not None
    metrics={
        "schema":1,"label":ns.label,"timestamp_utc":ts,"repo":str(repo),"base_commit":commit,
        "codex_home":env.get("CODEX_HOME"),"profile":ns.profile,"codex_exit_code":proc.returncode,
        "wall_seconds":wall,"eval_command":ns.eval_command,"eval_exit_code":eval_code,"eval_wall_seconds":eval_wall,
        "usage":usage,"per_turn_usage":per_turn,"root_responses":root_responses,"counts":counts,
        "derived":{"fresh_input_tokens_floor":max(input_t-cached_t,0) if cache_known else None,
                   "cache_ratio":cached_t/input_t if cache_known and input_t else None},
        "git":{"changed_files":changed_files,"insertions":ins,"deletions":dels},
        "command":cmd,"worktree":str(wt),
        "practice_feedback":collect_practice_feedback(run_dir)
    }
    (run_dir/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    print(json.dumps(metrics,indent=2))

    if not ns.keep_worktree:
        git(repo,"worktree","remove","--force",str(wt),capture=False)
    return proc.returncode if proc.returncode else (eval_code or 0)

if __name__=="__main__":
    raise SystemExit(main())
