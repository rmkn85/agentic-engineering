#!/usr/bin/env python3
"""A deliberately bounded, local Codex settings activity (Python 3.11+)."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
try:
    import tomllib
except ImportError:
    tomllib = None


class Rejected(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(path):
    path = Path(os.path.abspath(path))
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise Rejected('symlink path refused')
    return path


def read_regular(path):
    path = checked_path(path)
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise Rejected('regular file required')
        return stream.read(), stat.S_IMODE(info.st_mode)


def string_end(text, start):
    quote = text[start:start + 1]
    if quote not in ('"', "'"):
        raise Rejected('hint must use a TOML string value')
    delimiter = quote * 3 if text.startswith(quote * 3, start) else quote
    position = start + len(delimiter)
    while position < len(text):
        if quote == '"' and text[position] == '\\':
            position += 2
        elif text.startswith(delimiter, position):
            # TOML permits up to two extra quotes at a multiline terminator.
            position += len(delimiter)
            if len(delimiter) == 3:
                for _ in range(2):
                    if text[position:position + 1] == quote:
                        position += 1
            return position
        else:
            position += 1
    raise Rejected('unterminated hint string')


def transform(original, hint):
    if tomllib is None:
        raise Rejected('codex-settings activity requires Python 3.11+ (tomllib)')
    if not isinstance(hint, str) or not hint.strip() or len(hint.encode('utf-8')) > 65536:
        raise Rejected('hint must be nonempty UTF-8 text of at most 65536 bytes')
    text = original.decode('utf-8')
    before = tomllib.loads(text)
    try:
        old = before['features']['multi_agent_v2']['multi_agent_mode_hint_text']
        compact = before['model_auto_compact_token_limit']
    except (KeyError, TypeError):
        raise Rejected('required top-level compaction and explicit hint settings are missing')
    if not isinstance(old, str) or type(compact) is not int:
        raise Rejected('unsupported setting types')
    section = ''
    edits = []
    found = []
    offset = 0
    for line in text.splitlines(keepends=True):
        header = re.match(r'^\s*\[([^\]\n]+)\]\s*(?:#.*)?$', line.rstrip('\r\n'))
        if header:
            section = header.group(1).strip()
        key = re.match(r'^[ \t]*(model_auto_compact_token_limit|multi_agent_mode_hint_text)[ \t]*=[ \t]*', line)
        if key:
            name = key.group(1)
            if name == 'model_auto_compact_token_limit' and section == '':
                # Keep comments, indentation and newline; remove only the assignment.
                value = re.match(r'[+-]?[0-9_]+[ \t]*(?=#|\r?\n|$)', line[key.end():])
                if not value:
                    raise Rejected('unsupported compaction spelling')
                edits.append((offset, offset + key.end() + value.end(), ''))
                found.append(name)
            elif name == 'multi_agent_mode_hint_text' and section == 'features.multi_agent_v2':
                start = offset + key.end()
                end = string_end(text, start)
                edits.append((start, end, json.dumps(hint, ensure_ascii=False)))
                found.append(name)
        offset += len(line)
    if sorted(found) != ['model_auto_compact_token_limit', 'multi_agent_mode_hint_text']:
        raise Rejected('missing or ambiguous explicit setting assignments')
    result = text
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start] + replacement + result[end:]
    expected = copy.deepcopy(before)
    del expected['model_auto_compact_token_limit']
    expected['features']['multi_agent_v2']['multi_agent_mode_hint_text'] = hint
    if tomllib.loads(result) != expected:
        raise Rejected('transformation changed settings outside the allowed scope')
    return result.encode('utf-8')


def private_cache(cache):
    cache = checked_path(cache)
    try:
        cache.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = cache.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise Rejected('cache must be an owned private directory with mode 0700')
    return cache


def write_new(path, data, mode=0o600):
    checked_path(path)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def plan(config, hint_file, cache):
    hint_bytes, hint_mode = read_regular(hint_file)
    if hint_mode & 0o077 or checked_path(hint_file).stat().st_uid != os.getuid():
        raise Rejected('hint file must be owned and private (no group/other permissions)')
    hint = hint_bytes.decode('utf-8')
    original, _ = read_regular(config)
    result = transform(original, hint)
    payload = {'schema': 1, 'original_sha256': digest(original), 'result_sha256': digest(result),
               'remove_top_level': 'model_auto_compact_token_limit',
               'replace_hint': hint}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    receipt = digest(encoded)
    path = private_cache(cache) / (receipt + '.json')
    if path.exists():
        existing, mode = read_regular(path)
        if existing != encoded or mode != 0o600:
            raise Rejected('existing plan differs or is not private')
    else:
        write_new(path, encoded)
    return {'status': 'planned', 'plan_sha256': receipt, 'original_sha256': digest(original),
            'result_sha256': digest(result), 'actions': ['remove_top_level_compaction_override', 'replace_multi_agent_hint']}


def apply(config, receipt, cache):
    if not re.fullmatch(r'[0-9a-f]{64}', receipt):
        raise Rejected('PLAN_SHA256 must be 64 lowercase hexadecimal characters')
    cache = private_cache(cache)
    encoded, mode = read_regular(cache / (receipt + '.json'))
    if mode != 0o600 or digest(encoded) != receipt:
        raise Rejected('plan digest or private mode changed')
    payload = json.loads(encoded)
    if (set(payload) != {'schema', 'original_sha256', 'result_sha256', 'remove_top_level', 'replace_hint'}
            or payload['schema'] != 1 or payload['remove_top_level'] != 'model_auto_compact_token_limit'
            or not all(isinstance(payload[key], str) and re.fullmatch(r'[0-9a-f]{64}', payload[key])
                       for key in ('original_sha256', 'result_sha256'))):
        raise Rejected('unsupported plan scope')
    original, original_mode = read_regular(config)
    current = digest(original)
    if current == payload['result_sha256']:
        return {'status': 'already_applied', 'plan_sha256': receipt, 'result_sha256': current}
    if current != payload['original_sha256']:
        raise Rejected('config changed since planning')
    result = transform(original, payload['replace_hint'])
    if digest(result) != payload['result_sha256']:
        raise Rejected('planned result changed')
    backup = cache / (payload['original_sha256'] + '.backup')
    if backup.exists():
        saved, mode = read_regular(backup)
        if saved != original or mode != 0o600:
            raise Rejected('backup differs or is not private')
    else:
        write_new(backup, original)
    config = checked_path(config)
    descriptor, temporary = tempfile.mkstemp(prefix='.codex-settings-', dir=config.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            os.fchmod(stream.fileno(), original_mode)
            stream.write(result)
            stream.flush()
            os.fsync(stream.fileno())
        # Drift checks are not a lock against other writers.
        latest, latest_mode = read_regular(config)
        if latest != original or latest_mode != original_mode:
            raise Rejected('config changed before replacement')
        checked_path(cache)
        os.replace(temporary, config)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'status': 'applied', 'plan_sha256': receipt, 'result_sha256': digest(result), 'backup_sha256': digest(original)}


def parse_activity(arguments):
    if len(arguments) != 2:
        raise Rejected('expected exactly one activity and its declared KEY=value argument')
    activity, argument = arguments
    key = {'codex-settings-plan': 'HINT_FILE', 'codex-settings-apply': 'PLAN_SHA256'}.get(activity)
    if key is None or not argument.startswith(key + '=') or not argument[len(key) + 1:]:
        raise Rejected('unsupported activity or argument')
    value = argument[len(key) + 1:]
    if activity == 'codex-settings-apply' and not re.fullmatch(r'[0-9a-f]{64}', value):
        raise Rejected('PLAN_SHA256 must be 64 lowercase hexadecimal characters')
    return activity, value


def main(arguments=None):
    try:
        activity, value = parse_activity(sys.argv[1:] if arguments is None else arguments)
        if tomllib is None:
            raise Rejected('codex-settings activity requires Python 3.11+ (tomllib)')
        config = Path.home() / '.codex' / 'config.toml'
        cache = Path(tempfile.gettempdir()) / ('codex-settings-' + str(os.getuid()))
        result = plan(config, value, cache) if activity == 'codex-settings-plan' else apply(config, value, cache)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Rejected, OSError, ValueError, TypeError) as error:
        # Parser and OS errors can include private values; report only the class.
        message = str(error) if isinstance(error, Rejected) else type(error).__name__
        print('codex-settings: refused: ' + message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
