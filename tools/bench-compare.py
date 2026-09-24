#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from decimal import Decimal, InvalidOperation
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

def estimate_cost(tokens, rates):
    """API-equivalent estimate; input_tokens includes cached_input_tokens."""
    i,c,o,_=tokens
    if any(v is None for v in (i,c,o)) or c>i:
        return None
    return ((i-c)*rates[0]+c*rates[1]+o*rates[2])/Decimal(1_000_000)

def nonnegative_decimal(value):
    try:
        number=Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("rate must be a nonnegative number") from exc
    if not number.is_finite() or number<0:
        raise argparse.ArgumentTypeError("rate must be a nonnegative number")
    return number

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("metrics",nargs="+")
    ap.add_argument("--input-per-million", type=nonnegative_decimal)
    ap.add_argument("--cached-input-per-million", type=nonnegative_decimal)
    ap.add_argument("--output-per-million", type=nonnegative_decimal)
    ns=ap.parse_args()
    prices=(ns.input_per_million,ns.cached_input_per_million,ns.output_per_million)
    if any(v is not None for v in prices) and any(v is None for v in prices):
        ap.error("supply all three rates for a cost estimate")
    ms=[load(p) for p in ns.metrics]
    price_col=" API-equivalent cost |" if prices[0] is not None else ""
    price_rule="---:|" if prices[0] is not None else ""
    print(f"| label | accept | wall s | input | cached | cache % | output | reasoning | turns | commands | changed files | peak root input | compactions |{price_col}")
    print(f"|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|{price_rule}")
    for m in ms:
        i,c,o,r=tok(m); ratio=f"{100*c/i:.1f}%" if i is not None and c is not None and i>0 else "unavailable"
        accept=acceptance(m)
        q=m["counts"]; g=m["git"]
        root=m.get("root_responses") or {}
        peak=root.get("peak_input_tokens")
        compactions=root.get("compaction_count")
        price=estimate_cost((i,c,o,r),prices) if prices[0] is not None else None
        extra=f" {price:.4f} |" if price is not None else " unavailable |" if prices[0] is not None else ""
        print(f"| {m['label']} | {accept} | {m['wall_seconds']:.1f} | {display(i)} | {display(c)} | {ratio} | {display(o)} | {display(r)} | {q['turns']} | {q['commands']} | {g['changed_files']} | {display(peak)} | {display(compactions)} |{extra}")
if __name__=="__main__": main()
