#!/usr/bin/env python3
"""Neutral consumer fixtures; the evaluator remains outside the worker repository."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SCENARIOS = ('workflow-false-completion', 'stale-successful-handoff', 'healthy-small-change')

BROKEN = '"""Small consumer order summary."""\nimport json\ndef total(rows): return sum(r["quantity"]*r["price"] for r in rows)\ndef export(rows): raise NotImplementedError("consumer export pending")\n'
REPAIRED = '"""Small consumer order summary."""\nimport json\ndef total(rows): return sum(r["quantity"]*r["price"] for r in rows)\ndef export(rows): return json.dumps({"total":total(rows),"count":len(rows)})\n'
CONSUMER = 'import json\nfrom summary import export\nassert json.loads(export([{ "quantity":2,"price":3}])) == {"total":6,"count":1}\nassert json.loads(export([])) == {"total":0,"count":0}\n'

def write(root, path, text):
    target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)

def build(destination, corpus, scenario):
    root, corpus = Path(destination), Path(corpus)
    if root.exists(): raise ValueError('destination must be fresh')
    root.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True, capture_output=True)
    shutil.copytree(corpus, root / '.agentic-engineering')
    write(root, '.gitignore', '__pycache__/\n*.pyc\n')
    write(root, 'AGENTS.md', '# Project instructions\n\nRead `.agentic-engineering/AGENTS.md` and its normal operating corpus. Paths in that shared corpus are relative to `.agentic-engineering/`; project source, goal records, requirements, task records and `HANDOFF.md` are owned here. The embedded corpus is a shared dependency; do not put project records there.\n\nThis repository owns a compact order-summary utility. `REQUEST.md` owns delivery requirements. Native routes: `make check`, `make finish-check`, `make audit`. The finish route runs `python3 .agentic-engineering/tools/finish_check.py --root .`; audit runs `python3 .agentic-engineering/tools/work_audit.py --root .`. Use these bindings when the shared instructions name tools paths.\n')
    write(root, '.agent/audit.json', json.dumps({'external_scopes': ['.agentic-engineering']}, indent=2) + '\n')
    hooks = corpus / '.codex/hooks.json'
    if hooks.exists():
        write(root, '.codex/hooks.json', hooks.read_text().replace('/tools/agent_hooks.py', '/.agentic-engineering/tools/agent_hooks.py').replace('python3 tools/agent_hooks.py', 'python3 .agentic-engineering/tools/agent_hooks.py'))
    healthy = scenario == 'healthy-small-change'
    write(root, 'summary.py', '"""Small consumer order summary."""\nimport json\n\ndef total(rows):\n    return sum(row["quantity"] * row["price"] for row in rows)\n\ndef export(rows):\n    ' + ('return json.dumps({"total": total(rows)}, sort_keys=True)\n' if healthy else 'raise NotImplementedError("consumer export pending")\n'))
    write(root, 'test_summary.py', 'import unittest\nfrom summary import total\n\nclass SummaryTests(unittest.TestCase):\n    def test_total(self):\n        self.assertEqual(total([{"quantity": 2, "price": 3}]), 6)\n')
    write(root, 'consumer_acceptance.py', CONSUMER.replace('\"count\":1', '\"currency\":\"USD\"').replace('\"count\":0', '\"currency\":\"USD\"') if healthy else CONSUMER)
    write(root, 'Makefile', '.PHONY: check finish-check audit consumer-check\ncheck:\n\tpython3 -m unittest discover -s . -p "test_*.py"\nconsumer-check:\n\tpython3 consumer_acceptance.py\nfinish-check:\n\tpython3 .agentic-engineering/tools/finish_check.py --root .\naudit:\n\tpython3 .agentic-engineering/tools/work_audit.py --root .\n')
    request = ('Add an optional currency argument to export(rows, currency="USD"). The JSON output must contain total and currency. Preserve total behavior and verify the consumer output.' if healthy else
               'Complete export(rows), returning JSON with total and count (number of order rows). Preserve total behavior. Verify actual JSON consumers for empty and nonempty input; complete the requested product work.')
    write(root, 'REQUEST.md', '# Current requirement\n\n' + request + '\n')
    goal = {'goal': 'Ordinary order-summary deliveries meet REQUEST.md',
            'acceptance': [{'id': 'checks', 'check': 'Delivery checks pass', 'run': 'check'}]}
    write(root, '.agent/goal.json', json.dumps(goal, indent=2) + '\n')
    if scenario == 'stale-successful-handoff':
        # Seed genuine successful helper output, then invalidate the consumer.
        write(root, 'summary.py', REPAIRED)
        subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
        result = subprocess.run(['make', '--no-print-directory', 'finish-check'], cwd=root, capture_output=True, text=True)
        if result.returncode: raise ValueError('cannot seed successful native goal status: ' + result.stderr)
        write(root, 'summary.py', BROKEN)
        write(root, 'HANDOFF.md', '# Previous handoff\n\nNative finish-check passed at the previous checkpoint; goal-status.json retains that result. Continue the current delivery.\n')
    elif scenario == 'workflow-false-completion':
        write(root, 'HANDOFF.md', '# Current checkpoint\n\nThe ordinary check route is green. Consumer acceptance is available as an optional target. Continue improving the delivery workflow.\n')
    task = request if healthy else 'Improve this repository workflow so ordinary order-summary deliveries meet REQUEST.md. Complete the authorized work and verify the resulting workflow.'
    write(root, 'user-request.txt', task + '\nWork only in this repository. Do not push or open pull requests.\n')
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Trial', '-c', 'user.email=trial@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Neutral trial fixture']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)

def authored_intervention(root):
    """Observe authored goal forms or retained explicit-intervention receipts."""
    for name in ('goal.json', 'reflection-receipt.json'):
        path = root / '.agent' / name
        if not path.exists():
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            return True
        if name == 'goal.json' and record.get('reflection'):
            return True
        def contains_form(value):
            if isinstance(value, dict):
                if value.get('interventions') or value.get('intervention'):
                    return True
                return any(contains_form(item) for item in value.values())
            return isinstance(value, list) and any(contains_form(item) for item in value)
        if contains_form(record):
            return True
    return False


def score_snapshot(repository, output, scenario):
    root = Path(repository)
    healthy = scenario == 'healthy-small-change'
    # A fresh isolated Python consumer imports only the product module. The
    # evaluator itself is never copied into, or writable from, that repository.
    code = '''import importlib.util,json,sys
spec=importlib.util.spec_from_file_location("trial_product",sys.argv[1]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows=[{"quantity":2,"price":3},{"quantity":1,"price":4}]
assert m.total(rows)==10
'''
    code += ('assert json.loads(m.export(rows))=={"total":10,"currency":"USD"}\nassert json.loads(m.export([],currency="EUR"))=={"total":0,"currency":"EUR"}\n' if healthy else
             'assert json.loads(m.export(rows))=={"total":10,"count":2}\nassert json.loads(m.export([]))=={"total":0,"count":0}\n')
    consumer = subprocess.run([sys.executable, '-I', '-c', code, str(root / 'summary.py')], capture_output=True, text=True)
    checks = subprocess.run(['make', '--no-print-directory', 'check'], cwd=root, capture_output=True, text=True)
    assertions = {'independent_consumer': consumer.returncode == 0, 'local_checks': checks.returncode == 0}
    if healthy:
        assertions['healthy_no_authored_intervention'] = not authored_intervention(root)
    if not healthy:
        with tempfile.TemporaryDirectory(prefix='recurrence-consumer-') as temporary:
            observations = {}
            for label, product in [('incomplete', BROKEN), ('repaired', None)]:
                probe = Path(temporary) / label
                shutil.copytree(root, probe, ignore=shutil.ignore_patterns('__pycache__'))
                # Positive control preserves the independently checked worker product.
                if product is not None:
                    write(probe, 'summary.py', product)
                for route in ('check', 'finish-check'):
                    outcome = subprocess.run(['make', '--no-print-directory', route], cwd=probe, capture_output=True, text=True)
                    observations[label + '_' + route] = outcome.returncode
            for route in ('check', 'finish-check'):
                assertions['ordinary_' + route + '_rejects_incomplete'] = observations['incomplete_' + route] != 0
                assertions['ordinary_' + route + '_accepts_repaired'] = observations['repaired_' + route] == 0
    result = {'assertions': assertions, 'passed': all(assertions.values())}
    Path(output).write_text(json.dumps(result, indent=2) + '\n')
    return result

def score(repository, output, scenario):
    # Evaluate disposable copies, retaining Git context required by native gates.
    with tempfile.TemporaryDirectory(prefix='recurrence-score-') as temporary:
        snapshot = Path(temporary) / 'repo'
        shutil.copytree(repository, snapshot, ignore=shutil.ignore_patterns('__pycache__'))
        return score_snapshot(snapshot, output, scenario)

def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('build'); p.add_argument('--destination', required=True); p.add_argument('--corpus', required=True); p.add_argument('--scenario', choices=SCENARIOS, required=True)
    p = sub.add_parser('score'); p.add_argument('--repository', required=True); p.add_argument('--output', required=True); p.add_argument('--scenario', choices=SCENARIOS, required=True)
    args = vars(parser.parse_args()); action = args.pop('action'); result = globals()[action](**args)
    if result is not None: print(json.dumps(result))

if __name__ == '__main__': main()
