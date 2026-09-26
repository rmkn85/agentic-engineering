#!/usr/bin/env python3
"""Network-enabled, bounded real-upstream fixture. Not a model-benefit benchmark."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools/external_practices.py"


def main():
    parent = ROOT / ".agent-cache"
    parent.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="external-smoke-", dir=parent))
    repo, cache = work / "fixture", work / "cache"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitignore").write_text(".agent-cache/\n")
    (repo / "amounts.py").write_text("def sanitize_amount(amount):\n    return max(0, amount)\n")
    (repo / "billing.py").write_text("from amounts import sanitize_amount\n\ndef bill_total(amount):\n    return sanitize_amount(amount) * 2\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Fixture", "-c",
                    "user.email=fixture@example.invalid", "commit", "-qm", "upstream integration fixture"], check=True)
    prefix = [sys.executable, str(CLI), "--repo", str(repo), "--cache", str(cache)]
    checked = []

    def step(action, *positional, expected=0):
        args = prefix + [action] + list(positional) + ["--task", "upstream-smoke", "--kind", "fixture",
                    "--why", "Verify the pinned integration against a two-file fixture", "--timeout", "600"]
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=720)
        print(result.stdout.splitlines()[0] if result.stdout else "No command summary")
        header = json.loads(result.stdout.splitlines()[0])
        if result.returncode != expected:
            bundle = Path(header["receipt"]).parent if "receipt" in header else None
            if bundle:
                for log in bundle.glob("command-*.log"):
                    print("\n".join(log.read_text(errors="replace").splitlines()[-50:]))
            raise AssertionError("%s returned %d, expected %d" % (action, result.returncode, expected))
        checked.append(action + ":" + str(expected))
        return Path(header["receipt"]).parent

    try:
        step("setup", "ponytail")
        loaded = step("load")
        pin = json.loads((ROOT / "configs/external-practices.json").read_text())["ponytail"]
        original = cache / "upstream" / ("ponytail-" + pin["revision"]) / pin["skill"]
        assert (loaded / "upstream-skill.md").read_bytes() == original.read_bytes(), "upstream skill was changed"
        step("setup", "graphify")
        built = step("build")
        usage = json.loads((built / "execution.json").read_text())
        graph = json.loads((cache / usage["graph"]).read_text())
        nodes = graph["nodes"]
        def ids(name):
            return {str(node["id"]) for node in nodes
                    if name in str(node.get("label", node.get("name", node["id"])))}
        callers, callees = ids("bill_total"), ids("sanitize_amount")
        edges = graph.get("edges", graph.get("links", []))
        assert callers and callees, "expected fixture functions absent from graph"
        assert any(str(edge.get("source")) in callers and str(edge.get("target")) in callees
                   for edge in edges), "expected cross-file call relation absent"
        query = step("query", "sanitize_amount")
        response = (query / "command-00.log").read_text()
        assert "sanitize_amount" in response and ".py" in response, "query did not retrieve located source"
        step("explain", "sanitize_amount")
        step("path", "bill_total", "sanitize_amount")
        warm = step("build")
        warm_usage = json.loads((warm / "execution.json").read_text())
        assert warm_usage["cache_hit"] and not warm_usage["executions"], "warm build was not reused"
        with (repo / "amounts.py").open("a") as stream:
            stream.write("\ndef extra_amount():\n    return 1\n")
        step("query", "sanitize_amount", expected=2)
        step("build")
        step("query", "sanitize_amount")
        print("UPSTREAM_SMOKE_PASS: pinned skill, cross-file relation, scoped query, explain/path, reuse and invalidation")
        print("This is a fixture: no live model, development improvement or causal savings measured.")
        return 0
    finally:
        report = subprocess.run(prefix + ["report"], text=True, stdout=subprocess.PIPE, check=False)
        print(report.stdout)
        # Public CI runs only this public fixture; private task reports are never auto-uploaded.
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as stream:
                stream.write("\n## Upstream integration fixture\n\n" + report.stdout)
                stream.write("\nCompleted checks: " + ", ".join(checked) + "\n")
        print("Retained local fixture/evidence: " + str(work))


if __name__ == "__main__":
    raise SystemExit(main())
