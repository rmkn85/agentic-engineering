#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())

def tok(m):
    u=m.get("usage") or {}
    # Keep reasoning separate; client versions may account it differently in output_tokens.
    fields=("input_tokens","cached_input_tokens","output_tokens","reasoning_output_tokens")
    turns=m.get("per_turn_usage")
    def value(k):
        # Older metrics filled missing fields with zero. Their retained turn
        # records let us distinguish a measured zero from unavailable usage.
        if turns is not None and (not turns or any(not isinstance(t,dict) or type(t.get(k)) is not int for t in turns)):
            return None
        v=u.get(k)
        return v if type(v) is int and v>=0 else None
    return tuple(value(k) for k in fields)


def acceptance(m):
    if m.get("codex_exit_code")!=0 or m.get("eval_exit_code") not in (None,0):
        return "FAIL"
    return "PASS" if m.get("eval_command") and m.get("eval_exit_code")==0 else "UNVERIFIED"


def display(v): return str(v) if v is not None else "unavailable"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("metrics",nargs="+"); ns=ap.parse_args()
    ms=[load(p) for p in ns.metrics]
    print("| label | accept | wall s | input | cached | cache % | output | reasoning | turns | commands | changed files |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for m in ms:
        i,c,o,r=tok(m); ratio=f"{100*c/i:.1f}%" if i is not None and c is not None and i>0 else "unavailable"
        accept=acceptance(m)
        q=m["counts"]; g=m["git"]
        print(f"| {m['label']} | {accept} | {m['wall_seconds']:.1f} | {display(i)} | {display(c)} | {ratio} | {display(o)} | {display(r)} | {q['turns']} | {q['commands']} | {g['changed_files']} |")
if __name__=="__main__": main()
