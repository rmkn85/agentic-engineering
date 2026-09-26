#!/usr/bin/env python3
"""Bounded native subprocess experiment, NOT model-subagent/sandbox creation.

Requires an existing trusted Godot executable. No downloads or installations.
Uses disjoint writable projects/XDG paths, but all workers remain mutually trusted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import re
import subprocess
import time

HERE = Path(__file__).resolve().parent
PARAMETERS = [(4.9, 0.6, 0.05), (9.8, 1.2, 0.35), (19.6, 1.8, 0.65)]

def read_json(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def stop(proc):
    """Reap the owned process group; do not kill a user's other processes."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()

def context(pid):
    base = Path('/proc') / str(pid)
    namespaces = {}
    for name in ('mnt', 'pid', 'net', 'ipc', 'uts', 'user', 'cgroup'):
        try:
            namespaces[name] = os.readlink(base / 'ns' / name)
        except OSError:
            namespaces[name] = None
    try:
        cgroup = (base / 'cgroup').read_text()
    except OSError:
        cgroup = None
    return {'namespaces': namespaces, 'cgroup': cgroup}

def launch(engine, root, index, rendered, floor, start, affinity):
    d = root / f'worker-{index + 1}'
    d.mkdir(mode=0o700)
    project = d / 'project'
    project.mkdir()
    for name in ('project.godot', 'probe.gd'):
        shutil.copyfile(HERE / name, project / name)
    gravity, speed, hue = PARAMETERS[index]
    config = {'id': d.name, 'gravity': gravity, 'speed': speed, 'hue': hue,
              'floor': floor, 'frames': 180 if rendered else 6000, 'render': rendered}
    (d / 'config.json').write_text(json.dumps(config))
    # Allowlist the environment; do not copy credentials or personal configuration.
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': str(d / 'home'),
           'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
           'XDG_DATA_HOME': str(d / 'data'), 'XDG_CONFIG_HOME': str(d / 'config'),
           'XDG_CACHE_HOME': str(d / 'cache'), 'XDG_RUNTIME_DIR': str(d / 'runtime'),
           'PROBE_OUTPUT': str(d), 'PROBE_CONFIG': str(d / 'config.json'),
           'LIBGL_ALWAYS_SOFTWARE': '1', 'GALLIUM_DRIVER': 'llvmpipe',
           '__GLX_VENDOR_LIBRARY_NAME': 'mesa', 'LP_NUM_THREADS': '1',
           'GODOT_SILENCE_ROOT_WARNING': '1'}
    for name in ('home', 'runtime', 'data', 'config', 'cache'):
        (d / name).mkdir(mode=0o700)
    cmd = [str(engine), '--path', str(project), '--script', 'res://probe.gd',
           '--fixed-fps', '60', '--max-fps', '60', '--audio-driver', 'Dummy']
    if rendered:
        cmd += ['--display-driver', 'x11', '--rendering-method', 'gl_compatibility',
                '--rendering-driver', 'opengl3', '--resolution', '320x240', '--disable-vsync']
        cmd = ['xvfb-run', '-a', '-s', '-screen 0 320x240x24 -nolisten tcp', *cmd]
    else:
        cmd += ['--headless']
    # Bound this demonstration to one available CPU per worker, not a global setting.
    cmd = ['taskset', '-c', str(affinity[index % len(affinity)]), *cmd]
    log = (d / 'engine.log').open('wb')
    proc = subprocess.Popen(cmd, cwd=project, env=env, stdout=log,
                            stderr=subprocess.STDOUT, start_new_session=True)
    return {'proc': proc, 'dir': d, 'config': config, 'log': log,
            'launched_ms': (time.monotonic() - start) * 1000, 'cpu_samples': []}

def group(engine, root, count, rendered=False, floor=True, timeout=25):
    root.mkdir(parents=True, exist_ok=False)
    if not hasattr(os, 'sched_getaffinity'):
        raise RuntimeError('This Linux experiment needs CPU-affinity support')
    affinity = sorted(os.sched_getaffinity(0))
    start = time.monotonic()
    parent = context(os.getpid())
    workers = []
    peaks = {'sum_godot_rss_kib': 0, 'cgroup_memory_bytes': 0, 'simultaneous_progressing_workers': 0}
    def check_deadline():
        if time.monotonic() - start > timeout:
            raise TimeoutError('bounded native group exceeded its deadline')
    try:
        for index in range(count):
            workers.append(launch(engine, root, index, rendered, floor, start, affinity))
        while not all(read_json(w['dir'] / 'ready.json') for w in workers):
            check_deadline()
            if any(w['proc'].poll() is not None for w in workers):
                raise RuntimeError('worker exited before native readiness; inspect its engine.log')
            time.sleep(0.002)
        contexts = []
        for w in workers:
            ready = read_json(w['dir'] / 'ready.json')
            w['engine_pid'] = ready['pid']
            w['ready_ms'] = (time.monotonic() - start) * 1000
            contexts.append(context(ready['pid']))
            w['user_dir'] = ready['user_dir']
        for w in workers:
            (w['dir'] / 'go').write_text('run')
        while not all(w['proc'].poll() is not None for w in workers):
            check_deadline()
            total_rss = 0
            progressing = 0
            for w in workers:
                if w['proc'].poll() is not None:
                    w.setdefault('exit_ms', (time.monotonic() - start) * 1000)
                    continue
                if read_json(w['dir'] / 'started.json'):
                    w.setdefault('started_observed_ms', (time.monotonic() - start) * 1000)
                progress = read_json(w['dir'] / 'progress.json')
                if progress and 30 <= progress['ticks'] < w['config']['frames']:
                    progressing += 1
                try:
                    status = (Path('/proc') / str(w['engine_pid']) / 'status').read_text().splitlines()
                    rss = next(int(line.split()[1]) for line in status if line.startswith('VmRSS:'))
                    total_rss += rss
                    w['peak_rss_kib'] = max(w.get('peak_rss_kib', 0), rss)
                    stat = (Path('/proc') / str(w['engine_pid']) / 'stat').read_text().split(') ', 1)[1].split()
                    w['cpu_samples'].append(int(stat[11]) + int(stat[12]))
                except (OSError, StopIteration):
                    pass
            peaks['sum_godot_rss_kib'] = max(peaks['sum_godot_rss_kib'], total_rss)
            peaks['simultaneous_progressing_workers'] = max(peaks['simultaneous_progressing_workers'], progressing)
            try:
                mem = int(Path('/sys/fs/cgroup/memory.current').read_text())
                peaks['cgroup_memory_bytes'] = max(peaks['cgroup_memory_bytes'], mem)
            except OSError:
                pass
            time.sleep(0.002)
        result = []
        for w in workers:
            w['exit_ms'] = w.get('exit_ms', (time.monotonic() - start) * 1000)
            native = read_json(w['dir'] / 'result.json')
            if not native or native.get('config') != w['config'] or native.get('completed') is not True:
                raise RuntimeError('missing, incomplete or mismatched native result')
            engine_log = (w['dir'] / 'engine.log').read_text(errors='replace')
            if re.search(r'SCRIPT ERROR|Parse Error|(?:^|\n)ERROR:', engine_log):
                raise RuntimeError('native engine error; inspect retained evidence')
            expected_exit = 0 if floor else 1
            if w['proc'].returncode != expected_exit:
                raise RuntimeError('unexpected native exit; inspect retained evidence')
            checks = native.get('checks', {})
            required = {'completed_ticks', 'gravity_response', 'lateral_response', 'floor_contact', 'rests_above_floor', 'owned_user_state'}
            if rendered:
                required.update({'pixel_readback', 'software_renderer', 'png_saved'})
            if set(checks) != required or (floor and not all(value is True for value in checks.values())):
                raise RuntimeError('native checks did not complete successfully')
            if not floor and (checks.get('floor_contact') is not False or checks.get('rests_above_floor') is not False):
                raise RuntimeError('negative control did not reject missing collision')
            capture = native.get('capture')
            if rendered:
                from struct import unpack
                data = (w['dir'] / capture['file']).read_bytes()
                if hashlib.sha256(data).hexdigest() != capture['sha256'] or data[:8] != b'\x89PNG\r\n\x1a\n' or unpack('>II', data[16:24]) != (320, 240):
                    raise RuntimeError('capture transport contract failed')
                capture['bytes'] = len(data)
            del native['pid']
            cpu = w['cpu_samples']
            result.append({'worker': w['config']['id'], 'native': native, 'exit': w['proc'].returncode,
                           'launched_ms': w['launched_ms'], 'ready_ms': w['ready_ms'],
                           'started_observed_ms': w.get('started_observed_ms'), 'exit_ms': w['exit_ms'],
                           'cpu_seconds_observed': (max(cpu) - min(cpu)) / os.sysconf('SC_CLK_TCK') if cpu else None,
                           'peak_rss_kib': w.get('peak_rss_kib')})
        identity = {'distinct_engine_pids':len({w['engine_pid'] for w in workers}) == count,
                    'distinct_user_dirs':len({w['user_dir'] for w in workers}) == count,
                    'same_cgroup_membership_as_coordinator':all(c['cgroup'] == parent['cgroup'] for c in contexts),
                    'namespace_matches_coordinator':{n: all(c['namespaces'][n] is not None and c['namespaces'][n] == parent['namespaces'][n] for c in contexts) for n in parent['namespaces']}}
        overlap_ms = max(0, min(w['native']['active_finish_unix_usec'] for w in result) - max(w['native']['active_start_unix_usec'] for w in result)) / 1000
        summary = {'native_active_overlap_ms': overlap_ms, 'schema':1, 'kind':'native_processes_not_subagents', 'rendered':rendered,
                   'workers':result, 'identity':identity, 'peaks':peaks,
                   'wall_seconds':time.monotonic()-start, 'requested_clock_flags':'--fixed-fps 60 --max-fps 60 (not a real-time guarantee)',
                   'ai_subagents_spawned':0,'new_sandboxes_created':0}
        (root / 'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        return summary
    finally:
        for w in workers:
            stop(w['proc'])
            w['log'].close()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,choices=(1,2,3),default=1)
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--omit-floor',action='store_true')
    args=parser.parse_args()
    r=group(args.engine.resolve(),args.output.resolve(),args.workers,args.render,not args.omit_floor)
    print(json.dumps({k:r[k] for k in ('kind','wall_seconds','identity','peaks')},indent=2))
