#!/usr/bin/env python3
"""Hash-bound Context7-only native command switch and fixed-key official staging adoption."""
import copy
import difflib
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

from codex_settings import checked_path, read_regular, Rejected
from docs_result_cache import atomic, gate_lock
from context7_cache_stdio import PINNED_CHILD


def sha(data):
    return hashlib.sha256(data).hexdigest()


def transform(original, args, forward_api_key=False, api_key=None):
    before = tomllib.loads(original.decode())
    server = before.get("mcp_servers", {}).get("context7", {})
    if server.get("command") != "npx" or server.get("args") not in (["-y", "@upstash/context7-mcp"], PINNED_CHILD[1:]):
        raise Rejected("requires the reviewed Context7 stdio npx child; remote/auth migrations are separate")
    text = original.decode()
    block = re.search(r"(?m)^\[mcp_servers\.context7\][ \t]*(?:#.*)?\r?\n(?:(?!^\[).)*", text, re.S)
    if not block:
        raise Rejected("requires an explicit Context7 TOML section")
    section = block.group()
    command = re.compile(r'(?m)^([ \t]*command[ \t]*=[ \t]*)("(?:[^"\\]|\\.)*"|\'[^\']*\')')
    arguments = re.compile(r"(?m)^([ \t]*args[ \t]*=[ \t]*)\[[\s\S]*?\]")
    section, count_command = command.subn(lambda match: match.group(1) + json.dumps(sys.executable), section)
    section, count_args = arguments.subn(lambda match: match.group(1) + json.dumps(args), section)
    forwarded = server.get("env_vars", [])
    if forward_api_key:
        if not isinstance(forwarded, list) or any(not isinstance(name, str) for name in forwarded):
            raise Rejected("unsupported env_vars shape")
        forwarded = list(dict.fromkeys(forwarded + ["CONTEXT7_API_KEY"]))
        env_pattern = re.compile(r"(?m)^([ \t]*env_vars[ \t]*=[ \t]*)\[[\s\S]*?\]")
        if "env_vars" in server:
            section, count_env = env_pattern.subn(lambda match: match.group(1) + json.dumps(forwarded), section)
            if count_env != 1:
                raise Rejected("unsupported env_vars spelling")
        else:
            section = section.rstrip() + "\nenv_vars = " + json.dumps(forwarded) + "\n"
    if count_command != 1 or count_args != 1:
        raise Rejected("unsupported Context7 command/args spelling")
    candidate = (text[:block.start()] + section + text[block.end():]).encode()
    if api_key is not None:
        candidate = fixed_env_key(candidate, server, api_key)
    after = tomllib.loads(candidate.decode())
    expected = copy.deepcopy(before)
    expected["mcp_servers"]["context7"]["command"] = sys.executable
    expected["mcp_servers"]["context7"]["args"] = args
    if forward_api_key:
        expected["mcp_servers"]["context7"]["env_vars"] = forwarded
    if api_key is not None:
        expected["mcp_servers"]["context7"].setdefault("env", {})["CONTEXT7_API_KEY"] = api_key
    if after != expected:
        raise Rejected("transformation changed settings outside the supported Context7 launch/fixed-key scope")
    return candidate, server


def fixed_env_key(candidate, server, key):
    text = candidate.decode()
    block = re.search(r"(?m)^\[mcp_servers\.context7\.env\][ \t]*(?:#.*)?\r?\n(?:(?!^\[).)*", text, re.S)
    if "env" in server and (not isinstance(server["env"], dict) or block is None):
        raise Rejected("authenticated adoption requires a supported explicit env table")
    assignment = "CONTEXT7_API_KEY = " + json.dumps(key) + "\n"
    if block is None:
        return (text.rstrip() + "\n\n[mcp_servers.context7.env]\n" + assignment).encode()
    section = block.group()
    if "CONTEXT7_API_KEY" in server.get("env", {}):
        pattern = re.compile(r'(?m)^CONTEXT7_API_KEY[ \t]*=[ \t]*(?:"(?:[^"\\\n]|\\.)*"|\'[^\'\n]*\')[ \t]*(?:#.*)?(?:\r?\n|$)')
        section, count = pattern.subn(lambda _: assignment, section)
        if count != 1:
            raise Rejected("unsupported existing fixed env key spelling")
    else:
        section = section.rstrip() + "\n" + assignment
    return (text[:block.start()] + section + text[block.end():]).encode()


def staged_auth(spec):
    if "auth_config" not in spec:
        return None, None
    base = checked_path(Path(spec["workspace"]) / ".agent-cache" / "context7-auth")
    path = checked_path(spec["auth_config"])
    try:
        relative = path.relative_to(base)
    except ValueError:
        raise Rejected("auth input must stay inside private official staging")
    if len(relative.parts) < 3 or relative.parts[-2:] != (".codex", "config.toml"):
        raise Rejected("auth input must be an official staged project config")
    base_info = base.stat()
    if base_info.st_uid != os.getuid() or stat.S_IMODE(base_info.st_mode) != 0o700:
        raise Rejected("auth staging root must be owned and private")
    raw, mode = read_regular(path)
    if path.stat().st_uid != os.getuid() or mode != 0o600:
        raise Rejected("auth input must be owned mode0600")
    server = tomllib.loads(raw.decode()).get("mcp_servers", {}).get("context7", {})
    args = server.get("args", [])
    if server.get("command") != "npx" or not isinstance(args, list) or len(args) != 4 or args[:3] != ["-y", "@upstash/context7-mcp", "--api-key"]:
        raise Rejected("auth input does not contain the official stdio API-key pair")
    key = args[3]
    if not isinstance(key, str) or not re.fullmatch(r"ctx7sk[A-Za-z0-9_-]+", key):
        raise Rejected("auth input has an unsupported key shape")
    return key, sha(raw)


def validate_spec(spec):
    required = {"config", "workspace", "repository", "namespace", "max_age", "valid_for"}
    if not required <= set(spec) or set(spec) - required - {"forward_api_key", "auth_config"} or type(spec.get("forward_api_key", False)) is not bool:
        raise Rejected("unsupported plan specification")
    if "auth_config" in spec and (not isinstance(spec["auth_config"], str) or spec["namespace"] != "context7-stdio-cli-auth"):
        raise Rejected("official staged auth requires its fixed authenticated namespace")
    for key in ("config", "workspace", "repository"):
        if not Path(spec[key]).is_absolute():
            raise Rejected("plan paths must be absolute")
        checked_path(spec[key])
    if not isinstance(spec["namespace"], str) or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}", spec["namespace"]):
        raise Rejected("nonsecret fixed namespace label required")
    for key in ("max_age", "valid_for"):
        if type(spec[key]) is not int or not 0 < spec[key] <= 604800:
            raise Rejected("reviewed freshness must be 1..604800 seconds")


def source_paths(spec):
    tools = Path(spec["repository"]) / "tools"
    return [tools / name for name in ("context7_cache_stdio.py", "docs_result_cache.py", "context7_cache_config.py", "codex_settings.py", "make")]


def launch_args(spec):
    script = Path(spec["repository"]) / "tools" / "context7_cache_stdio.py"
    return [str(script), "--cache-dir", str(Path(spec["workspace"]) / ".agent-cache" / "docs-results"), "--namespace", spec["namespace"], "--source", "@upstash/context7-mcp@4.4.2;context7-api-v2", "--max-age", str(spec["max_age"]), "--valid-for", str(spec["valid_for"])]


def host_identity(spec):
    repo = Path(__file__).resolve().parents[1]
    if (spec.get("repository") != str(repo) or spec.get("workspace") != str(repo.parent) or spec.get("config") != str(Path.home() / ".codex" / "config.toml")):
        raise Rejected("plan does not target the canonical repository, workspace and native config")


def private_store(store):
    checked_path(store)
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = store.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise Rejected("plan store must be an owned private directory")


def plan(spec_path, store):
    if tomllib is None:
        raise Rejected("config activity requires Python 3.11+ (tomllib)")
    private_store(store)
    spec_bytes, _ = read_regular(spec_path)
    spec = json.loads(spec_bytes)
    validate_spec(spec)
    repo = Path(spec["repository"])
    script = repo / "tools" / "context7_cache_stdio.py"
    sources = {str(path): sha(read_regular(path)[0]) for path in source_paths(spec)}
    original, mode = read_regular(spec["config"])
    args = launch_args(spec)
    key, auth_sha = staged_auth(spec)
    if key is not None and (mode != 0o600 or Path(spec["config"]).stat().st_uid != os.getuid()):
        raise Rejected("native config must be private mode0600 before fixed-key adoption")
    candidate, old_server = transform(original, args, spec.get("forward_api_key", False), key)
    body = {"spec": spec, "spec_sha256": sha(spec_bytes), "original_sha256": sha(original), "candidate": candidate.decode(), "candidate_sha256": sha(candidate), "mode": mode, "sources": sources, "auth_sha256": auth_sha}
    identity = sha(json.dumps(body, sort_keys=True).encode())
    atomic(store / (identity + ".json"), body)
    # Only expose reviewed changed fields; never copy unrelated config or env values.
    old_view = {"command": old_server["command"], "args": old_server["args"]}
    new_view = {"command": sys.executable, "args": args}
    if spec.get("forward_api_key", False):
        old_view["env_vars"] = old_server.get("env_vars", [])
        new_view["env_vars"] = list(dict.fromkeys(old_view["env_vars"] + ["CONTEXT7_API_KEY"]))
    if key is not None:
        old_view["env.CONTEXT7_API_KEY"] = "<present; redacted>" if "CONTEXT7_API_KEY" in old_server.get("env", {}) else "<absent>"
        new_view["env.CONTEXT7_API_KEY"] = "<official staged key; redacted>"
    old = json.dumps(old_view, indent=2).splitlines(True)
    new = json.dumps(new_view, indent=2).splitlines(True)
    return {"plan_sha256": identity, "auth_input_sha256": auth_sha, "plan_file": str(store / (identity + ".json")), "diff": "".join(difflib.unified_diff(old, new, fromfile="context7-before", tofile="context7-after")), "activation": "requires a new native MCP client/session; no hot reload claim"}


def apply(identity, store):
    if not re.fullmatch(r"[0-9a-f]{64}", identity):
        raise Rejected("invalid plan hash")
    private_store(store)
    body = json.loads(read_regular(store / (identity + ".json"))[0])
    if set(body) != {"spec", "spec_sha256", "original_sha256", "candidate", "candidate_sha256", "mode", "sources", "auth_sha256"}:
        raise Rejected("unsupported plan schema")
    if sha(json.dumps(body, sort_keys=True).encode()) != identity:
        raise Rejected("plan hash mismatch")
    validate_spec(body["spec"])
    if set(body["sources"]) != {str(path) for path in source_paths(body["spec"])}:
        raise Rejected("reviewed source set mismatch")
    for path, expected in body["sources"].items():
        if sha(read_regular(path)[0]) != expected:
            raise Rejected("reviewed source changed; regenerate plan")
    config = checked_path(body["spec"]["config"])
    candidate = body["candidate"].encode()
    if sha(candidate) != body["candidate_sha256"]:
        raise Rejected("candidate hash mismatch")
    with gate_lock(store / "apply.json"):
        current, mode = read_regular(config)
        if sha(current) != body["original_sha256"] or mode != body["mode"]:
            raise Rejected("configuration changed; regenerate plan")
        key, auth_sha = staged_auth(body["spec"])
        if key is not None and (mode != 0o600 or config.stat().st_uid != os.getuid()):
            raise Rejected("native config must be private mode0600 before fixed-key adoption")
        if auth_sha != body["auth_sha256"]:
            raise Rejected("official staged auth input changed; regenerate plan")
        expected, _ = transform(current, launch_args(body["spec"]), body["spec"].get("forward_api_key", False), key)
        if expected != candidate:
            raise Rejected("candidate differs from the supported Context7-only transformation")
        backup = store / (identity + ".before.json")
        atomic(backup, {"original": current.decode()})
        descriptor, temporary = tempfile.mkstemp(prefix=".context7-cache-", dir=config.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                os.fchmod(stream.fileno(), mode)
                stream.write(candidate)
                stream.flush()
                os.fsync(stream.fileno())
            if sha(read_regular(config)[0]) != body["original_sha256"]:
                raise Rejected("configuration changed during apply")
            os.replace(temporary, config)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return {"status": "applied", "config_sha256": sha(candidate), "backup": str(backup), "activation": "new native MCP client/session required"}


def main(arguments=None):
    try:
        values = sys.argv[1:] if arguments is None else arguments
        if len(values) != 2:
            raise Rejected("expected one activity and one KEY=value argument")
        activity, argument = values
        store = Path(tempfile.gettempdir()) / ("context7-cache-config-" + str(os.getuid()))
        if activity == "context7-cache-plan" and argument.startswith("SPEC_FILE="):
            spec_path = argument[len("SPEC_FILE="):]
            host_identity(json.loads(read_regular(spec_path)[0]))
            result = plan(spec_path, store)
        elif activity == "context7-cache-apply" and argument.startswith("PLAN_SHA256="):
            identity = argument[len("PLAN_SHA256="):]
            if not re.fullmatch(r"[0-9a-f]{64}", identity):
                raise Rejected("invalid plan hash")
            private_store(store)
            host_identity(json.loads(read_regular(store / (identity + ".json"))[0])["spec"])
            result = apply(identity, store)
        else:
            raise Rejected("unsupported Context7 activity")
        print(json.dumps(result, sort_keys=True))
        return 0
    except (Rejected, OSError, ValueError, TypeError, KeyError) as error:
        print("context7-cache-config: refused: " + (str(error) if isinstance(error, Rejected) else type(error).__name__), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
