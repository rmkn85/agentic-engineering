#!/usr/bin/env python3
"""Repeat the native fixture inside an already configured, authorized workspace.

No installation, network requests, driver override, new sandbox or model call.
Raw evidence is temporary; only allowlisted results leave the owned directory.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
FIXTURE = HERE.parent / 'chatgpt-parallel-native-processes-2026-09'
EXPECTED = {'probe.gd': '83776691d735fd17cdd2f2e80744c9348b298ee1',
            'project.godot': '6cc9ccb3269a440c0e0d45e5d47a96b6df3d9ee6'}


def verify_fixture():
    for name, expected in EXPECTED.items():
        data = (FIXTURE / name).read_bytes()
        digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if digest != expected:
            raise ValueError('Fixture changed; review comparability before running: ' + name)


def safe_error(log):
    """Keep diagnosis useful without copying a host inventory or private paths."""
    if 'error while loading shared libraries:' in log:
        text = log.split('error while loading shared libraries:', 1)[1].splitlines()[0]
        return 'shared-library startup failure: ' + re.sub(r'/[^\s]+', '<path>', text)[:240]
    lines = [line.strip() for line in log.splitlines()
             if any(x in line.lower() for x in ('error', 'failed', 'cannot', 'not found'))]
    return [re.sub(r'/[^\s]+', '<path>', line)[:240] for line in lines[:4]]


def compact(label, result):
    workers=[]
    for worker in result['workers']:
        native=worker['native']
        row={key:native[key] for key in ('config','engine','display','renderer','ticks',
             'simulation_seconds','contacts','early_y','early_x','final_y','final_x','checks','capture')}
        row.update(exit=worker['exit'], cpu_seconds_observed=worker['cpu_seconds_observed'],
                   peak_rss_kib=worker['peak_rss_kib'])
        if 'adapter' in native:
            name=native['adapter'].lower()
            row['adapter_class']='llvmpipe' if 'llvmpipe' in name else 'other_not_disclosed'
        workers.append(row)
    return {'case':label,'status':'PASS','wall_seconds':result['wall_seconds'],
            'native_active_overlap_ms':result['native_active_overlap_ms'],
            'identity':result['identity'],'peaks':result['peaks'],'workers':workers,
            'driver_policy':result['driver_policy'],'visual_inspection':'unperformed'}


def run(workspace: Path, include_render=True):
    workspace=workspace.resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError('An existing authorized workspace is required')
    verify_fixture()
    spec=importlib.util.spec_from_file_location('bounded_native_pool', FIXTURE/'run.py')
    pool=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pool)
    declared=os.environ.get('GODOT_BIN') or os.environ.get('GODOT')
    engine=shutil.which(declared) if declared else (shutil.which('godot') or shutil.which('godot4'))
    receipt={'schema':1,'status':'BLOCKED','scope':'configured-runner-native-case-study',
             'python':platform.python_version(),'platform':platform.system(),'architecture':platform.machine(),
             'non_root':os.geteuid()!=0,'engine_available':bool(engine),
             'driver_policy':'inherited_configuration','driver_variables_inherited':
                  [k for k in pool.DRIVER_KEYS if k in os.environ],
             'fixture_git_blobs':EXPECTED,'cases':[], 'network_requests_by_probe':0,
             'ai_subagents_spawned':0,'new_sandboxes_created':0,'artifacts_uploaded':0}
    if not engine:
        receipt['reason']='No configured Godot executable; no install or host search attempted'
        return receipt
    required=['taskset'] + (['xvfb-run','xauth'] if include_render else [])
    missing=[name for name in required if not shutil.which(name)]
    if missing:
        receipt['reason']='Missing existing tools: '+', '.join(missing)
        return receipt
    digest=hashlib.sha256()
    with open(engine,'rb') as binary:
        for chunk in iter(lambda: binary.read(1024*1024), b''):
            digest.update(chunk)
    receipt['engine_sha256']=digest.hexdigest()
    with tempfile.TemporaryDirectory(prefix='.native-comparison-',dir=workspace) as temp:
        root=Path(temp)
        cases=[('headless-pilot',1,False,True),('headless-parallel',3,False,True),
               ('headless-no-floor',1,False,False)]
        if include_render:
            cases += [('render-pilot',1,True,True),('render-parallel',3,True,True)]
        for label, count, rendered, floor in cases:
            try:
                result=pool.group(Path(engine),root/label,count,rendered,floor,configured_drivers=True)
                row=compact(label,result)
                receipt['cases'].append(row)
                print('NATIVE_CASE '+json.dumps(row,separators=(',',':')),flush=True)
            except (OSError,RuntimeError,ValueError,TimeoutError) as error:
                logs=[]
                for index in range(1,count+1):
                    logfile=root/label/f'worker-{index}'/'engine.log'
                    if logfile.is_file():
                        logs.append({'worker':index,'diagnostic':safe_error(logfile.read_text(errors='replace'))})
                receipt['cases'].append({'case':label,'status':'FAIL','error_type':type(error).__name__,'logs':logs})
                receipt['status']='FAIL'
                break
        else:
            receipt['status']='PASS'
        receipt['temporary_evidence_bytes']=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    receipt['temporary_evidence_cleaned']=True
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--headless-only',action='store_true')
    args=parser.parse_args()
    result=run(args.workspace,not args.headless_only)
    print('RUNNER_NATIVE_COMPARISON '+json.dumps(result,separators=(',',':')),flush=True)
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as out:
            out.write('### Native comparison\n```json\n'+json.dumps(result,indent=2)+'\n```\n')
    raise SystemExit(0 if result['status']=='PASS' else 2 if result['status']=='BLOCKED' else 1)
