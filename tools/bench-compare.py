#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())

def tok(m):
    u=m["usage"]
    # Keep reasoning separate; client versions may account it differently in output_tokens.
    return u.get("input_tokens",0),u.get("cached_input_tokens",0),u.get("output_tokens",0),u.get("reasoning_output_tokens",0)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("metrics",nargs="+"); ns=ap.parse_args()
    ms=[load(p) for p in ns.metrics]
    print("| label | accept | wall s | input | cached | cache % | output | reasoning | turns | commands | changed files |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for m in ms:
        i,c,o,r=tok(m); ratio=(100*c/i) if i else 0
        accept=m.get("eval_exit_code") in (None,0) and m.get("codex_exit_code")==0
        q=m["counts"]; g=m["git"]
        print(f"| {m['label']} | {'PASS' if accept else 'FAIL'} | {m['wall_seconds']:.1f} | {i} | {c} | {ratio:.1f}% | {o} | {r} | {q['turns']} | {q['commands']} | {g['changed_files']} |")
if __name__=="__main__": main()
