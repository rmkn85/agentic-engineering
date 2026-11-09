#!/usr/bin/env python3
"""Native, fresh-session trials. Private execution material stays outside the corpus.

No sandbox, trust, rules, or user-config overrides are supplied to Codex. A
preflight observes prerequisites; it cannot grant hook trust or prove adherence.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

MODEL = "gpt-6.1-sol"
EFFORT = "medium"

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def command(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)

def tree_hash(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(Path(root).rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(root).parts and '__pycache__' not in p.parts}

def append(audit, row):
    with (Path(audit) / 'attempts.jsonl').open('a') as out:
        out.write(json.dumps(row, sort_keys=True) + '\n')

def host_controls():
    home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    files = [home / 'config.toml', home / 'hooks.json']
    files += sorted((home / 'rules').glob('*.rules'))
    return {str(p.relative_to(home)): digest(p) for p in files if p.is_file()}

def preflight(repository, codex='codex', trust_receipt=None):
    repository = Path(repository).resolve()
    version = command([codex, '--version'])
    help_result = command([codex, 'exec', '--help'])
    login = command([codex, 'login', 'status'])
    home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    cache = home / 'models_cache.json'
    try:
        models = json.loads(cache.read_text()).get('models', [])
        available = any(m.get('slug') == MODEL and any(
            e.get('effort') == EFFORT for e in m.get('supported_reasoning_levels', [])) for m in models)
    except (OSError, ValueError, AttributeError):
        available = None
    discovery = [p for p in [repository / 'AGENTS.md', repository / '.codex/hooks.json',
                            home / 'hooks.json', home / 'config.toml'] if p.is_file()]
    trust = None
    if trust_receipt:
        trust = json.loads(Path(trust_receipt).read_text())
        if trust.get('native_hook_trust') != 'confirmed':
            raise ValueError('trust receipt must record native_hook_trust=confirmed; runner never grants trust')
    hooks = repository / '.codex/hooks.json'
    return {'cli_version': version.stdout.strip(), 'cli_available': version.returncode == 0,
            'ephemeral_supported': '--ephemeral' in help_result.stdout,
            'host_controls': host_controls(),
            'required_cli_flags': all(f in help_result.stdout for f in ('--json', '--model', '--cd')),
            'authenticated': login.returncode == 0, 'model': MODEL, 'effort': EFFORT,
            'cached_model_available': available, 'instruction_discovery': 'native AGENTS.md',
            'discovered_files': {p.name if p.parent == home else str(p.relative_to(repository)): digest(p) for p in discovery},
            'hook_config_present': hooks.exists(), 'native_hook_trust': 'reported_confirmed' if trust else 'unknown',
            'hook_invocation_observed': False,
            'trust_receipt_sha256': digest(trust_receipt) if trust_receipt else None,
            'limitations': ['Cached availability is not a successful model request.',
                            'Discovery and trust receipts do not prove hooks executed.']}

def prepare(source, ref, builder, scenario, repository, audit, arm, pair, evaluator, baseline_ref, candidate_ref):
    source, repository, audit = Path(source).resolve(), Path(repository).resolve(), Path(audit).resolve()
    builder, evaluator = Path(builder).resolve(), Path(evaluator).resolve()
    if repository.exists() or audit.exists():
        raise ValueError('repository and audit must be fresh paths')
    if audit == repository or repository in audit.parents or repository in evaluator.parents:
        raise ValueError('audit and evaluator must be outside the worker repository')
    commit = command(['git', 'rev-parse', ref + '^{commit}'], source)
    if commit.returncode:
        raise ValueError('source commit not available')
    identities = {}
    for name, value in [('baseline', baseline_ref), ('candidate', candidate_ref)]:
        resolved = command(['git', 'rev-parse', value + '^{commit}'], source)
        if resolved.returncode: raise ValueError('arm source unavailable')
        identities[name] = resolved.stdout.strip()
    if arm not in identities or identities[arm] != commit.stdout.strip():
        raise ValueError('arm does not match frozen source identity')
    audit.mkdir(parents=True)
    corpus = audit / 'corpus'; corpus.mkdir()
    archive = subprocess.Popen(['git', 'archive', commit.stdout.strip()], cwd=source, stdout=subprocess.PIPE)
    extracted = subprocess.run(['tar', '-x', '-C', str(corpus)], stdin=archive.stdout, capture_output=True)
    archive.stdout.close()
    if archive.wait() or extracted.returncode:
        raise ValueError('source archive failed')
    result = command([sys.executable, str(builder), 'build', '--destination', str(repository), '--corpus', str(corpus), '--scenario', scenario])
    (audit / 'build.stdout').write_text(result.stdout); (audit / 'build.stderr').write_text(result.stderr)
    if result.returncode:
        append(audit, {'phase': 'prepare', 'status': 'failed', 'returncode': result.returncode})
        raise ValueError('builder failed; see private audit logs')
    prompt = (repository / 'user-request.txt').read_text()
    (audit / 'prompt.txt').write_text(prompt)
    snapshot = tree_hash(repository)
    # These are immutable experimental controls, independent of product files.
    protected = {p: h for p, h in snapshot.items() if p in ('Makefile', 'AGENTS.md', 'REQUEST.md', 'user-request.txt') or
                 p.startswith('.codex/') or p.startswith('.agentic-engineering/')}
    spec = {'schema': 1, 'pair': pair, 'arm': arm, 'scenario': scenario,
            'source_commit': commit.stdout.strip(), 'source_commits': identities, 'model': MODEL, 'effort': EFFORT,
            'builder_sha256': digest(builder), 'evaluator_sha256': digest(evaluator),
            'prompt_sha256': digest(audit / 'prompt.txt'), 'fixture': snapshot, 'protected': protected,
            'host_controls': host_controls(),
            'conditions': {'fresh_session': True, 'instructions': 'native AGENTS discovery',
                           'host_configuration': 'inherited unchanged', 'permission_policy': 'inherited unchanged', 'ephemeral': True}}
    write(audit / 'spec.json', spec)
    write(audit / 'private.json', {'repository': str(repository), 'evaluator': str(evaluator), 'builder': str(builder)})
    write(audit / 'seal.json', {'spec_sha256': digest(audit / 'spec.json')})
    return spec

def load(audit):
    audit = Path(audit).resolve()
    seal = json.loads((audit / 'seal.json').read_text())
    if digest(audit / 'spec.json') != seal['spec_sha256']:
        raise ValueError('frozen specification changed')
    spec = json.loads((audit / 'spec.json').read_text())
    private = json.loads((audit / 'private.json').read_text())
    if digest(private['evaluator']) != spec['evaluator_sha256'] or digest(private['builder']) != spec['builder_sha256']:
        raise ValueError('builder/evaluator changed after freeze')
    if digest(audit / 'prompt.txt') != spec['prompt_sha256']:
        raise ValueError('prompt changed after freeze')
    return audit, spec, private

def run(audit, codex='codex', trust_receipt=None):
    audit, spec, private = load(audit)
    repository = Path(private['repository'])
    check = preflight(repository, codex, trust_receipt)
    write(audit / 'preflight.json', check)
    attempt = {'attempt': str(uuid.uuid4()), 'phase': 'run', 'status': 'started',
               'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'human_assistance': [],
               'usage': None, 'wall_seconds': None, 'selected_actions': [], 'hook_calls': None, 'hook_adapter_events': None,
               'runtime_settings': {'model': None, 'effort': None}, 'host_controls_match': check.get('host_controls') == spec['host_controls']}
    append(audit, attempt)
    if not attempt['host_controls_match']:
        attempt.update(status='host_controls_changed'); append(audit, attempt); return attempt
    if not (check['cli_available'] and check['required_cli_flags'] and check.get('ephemeral_supported', False) and check['authenticated']) or check['cached_model_available'] is False:
        attempt.update(status='preflight_failed'); append(audit, attempt); return attempt
    if check['hook_config_present'] and check['native_hook_trust'] != 'reported_confirmed':
        attempt.update(status='native_hook_trust_required'); append(audit, attempt); return attempt
    args = [codex, 'exec', '--json', '--ephemeral', '-C', str(repository), '-m', MODEL,
            '-c', 'model_reasoning_effort="medium"', '-']
    started = time.monotonic()
    try:
        with (audit / (attempt['attempt'] + '.jsonl')).open('w') as stdout, (audit / (attempt['attempt'] + '.stderr')).open('w') as stderr:
            result = subprocess.run(args, input=(audit / 'prompt.txt').read_text(), text=True,
                                    stdout=stdout, stderr=stderr, check=False)
        attempt.update(status='completed' if result.returncode == 0 else 'failed', returncode=result.returncode)
    except (KeyboardInterrupt, OSError) as exc:
        attempt.update(status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed', error_type=type(exc).__name__)
    attempt['wall_seconds'] = round(time.monotonic() - started, 3)
    log = audit / (attempt['attempt'] + '.jsonl')
    if log.exists():
        for line in log.read_text().splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            if event.get('type') == 'turn.completed': attempt['usage'] = event.get('usage')
            if event.get('type', '').startswith('hook.'):
                if attempt['hook_calls'] is None: attempt['hook_calls'] = []
                attempt['hook_calls'].append(event.get('type'))
            if isinstance(event.get('model'), str): attempt['runtime_settings']['model'] = event['model']
            if isinstance(event.get('reasoning_effort'), str): attempt['runtime_settings']['effort'] = event['reasoning_effort']
            item = event.get('item', {})
            if item.get('type') == 'command_execution' and event.get('type') == 'item.completed':
                attempt['selected_actions'].append(item.get('command'))
    adapter_log = repository / '.agent/hook-events.jsonl'
    if adapter_log.is_file():
        events = []
        for line in adapter_log.read_text().splitlines():
            try: entry = json.loads(line)
            except ValueError: continue
            if entry.get('schema') == 'agent-hook-event/v1':
                events.append({k: entry.get(k) for k in ('host', 'event', 'adapter_sha256', 'decision')})
        attempt['hook_adapter_events'] = events
        # Adapter records alone cannot prove native host invocation.
    append(audit, attempt)
    return attempt

def score(audit):
    audit, spec, private = load(audit)
    repo = Path(private['repository'])
    integrity = all((repo / p).is_file() and digest(repo / p) == h for p, h in spec['protected'].items())
    output = audit / ('score-' + str(uuid.uuid4()) + '.json')
    result = command([sys.executable, private['evaluator'], 'score', '--repository', str(repo), '--output', str(output), '--scenario', spec['scenario']])
    (output.with_suffix('.stdout')).write_text(result.stdout)
    (output.with_suffix('.stderr')).write_text(result.stderr)
    try:
        raw = json.loads(output.read_text()) if output.exists() else {}
    except ValueError:
        raw = {}
    if not isinstance(raw, dict): raw = {}
    assertions = raw.get('assertions', {})
    valid = bool(assertions) and all(type(v) is bool for v in assertions.values())
    receipt = {'phase': 'score', 'scenario': spec['scenario'], 'pair': spec['pair'], 'arm': spec['arm'],
               'source_commit': spec['source_commit'], 'spec_sha256': digest(audit / 'spec.json'),
               'integrity': integrity, 'assertions': assertions if valid else {},
               'evaluator_returncode': result.returncode,
               'status': 'scored' if valid else 'inconclusive',
               'passed': integrity and result.returncode == 0 and valid and all(assertions.values()) and raw.get('passed') is True}
    append(audit, receipt); write(audit / 'receipt.json', receipt)
    return receipt

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('preflight'); p.add_argument('--repository', required=True); p.add_argument('--codex', default='codex'); p.add_argument('--trust-receipt')
    p = sub.add_parser('prepare')
    for name in ('source', 'ref', 'builder', 'scenario', 'repository', 'audit', 'arm', 'pair', 'evaluator', 'baseline-ref', 'candidate-ref'): p.add_argument('--' + name, required=True)
    p = sub.add_parser('run'); p.add_argument('--audit', required=True); p.add_argument('--codex', default='codex'); p.add_argument('--trust-receipt')
    p = sub.add_parser('score'); p.add_argument('--audit', required=True)
    args = vars(parser.parse_args(argv)); action = args.pop('action')
    try:
        print(json.dumps(globals()[action](**args), sort_keys=True)); return 0
    except (OSError, ValueError, KeyError) as exc:
        if args.get('audit') and Path(args['audit']).is_dir():
            append(args['audit'], {'phase': action, 'status': 'inconclusive', 'error_type': type(exc).__name__})
        print('native trial: ' + str(exc), file=sys.stderr); return 1

if __name__ == '__main__': raise SystemExit(main())
