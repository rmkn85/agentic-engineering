"""Observe inherited Linux containment without probing other processes or changing it."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

MODES = ('native', 'outer-codex-sandbox')


def observe(mode):
    if mode not in MODES:
        raise ValueError('unknown execution boundary')
    if mode == 'native':
        return {'mode': mode, 'status': 'not_applicable'}
    checks = {}
    result = {'mode': mode, 'status': 'failed', 'checks': checks,
              'limitations': ['Observations identify expected inherited containment, not its complete policy.',
                              'Environment alone is not containment proof.',
                              'No model tool use, workspace write or consumer acceptance is proved.']}
    try:
        checks['linux'] = sys.platform.startswith('linux')
        if not checks['linux']:
            return result
        checks['root_readonly'] = bool(os.statvfs('/').f_flag & os.ST_RDONLY)
        mask = Path('/tmp') / ('codex-daemon-' + str(os.geteuid()))
        info = mask.lstat()
        checks['reserved_mask_owned_directory_mode000'] = (
            stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0)
        checks['reserved_mask_readonly'] = bool(os.statvfs(mask).f_flag & os.ST_RDONLY)
        status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
        checks['no_new_privileges'] = status.get('NoNewPrivs', '').strip() == '1'
        checks['seccomp_filter'] = status.get('Seccomp', '').strip() == '2'
        profile = os.environ.get('CODEX_PERMISSION_PROFILE', '')
        checks['inherited_profile_present'] = bool(profile.strip())
        result['profile_sha256'] = hashlib.sha256(profile.encode()).hexdigest()
        result['mount_namespace'] = os.readlink('/proc/self/ns/mnt')
        if all(checks.values()):
            result['status'] = 'verified'
            # Namespace identifiers vary across ordinary tool executions. Bind only stable observations.
            signature = {'mode': mode, 'checks': checks, 'profile_sha256': result['profile_sha256']}
            result['signature_sha256'] = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    except (OSError, ValueError) as exc:
        result['error_type'] = type(exc).__name__
    return result


def matches(frozen, current):
    return (frozen.get('status') == 'verified' and current.get('status') == 'verified'
            and bool(frozen.get('signature_sha256'))
            and frozen['signature_sha256'] == current.get('signature_sha256'))
