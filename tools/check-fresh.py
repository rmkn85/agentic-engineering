#!/usr/bin/env python3
"""Run an explicit trusted native check from fresh and stale disposable clones.

This verifies committed source, not model behavior, remote auth or deployment.
It changes no contributor checkout and never pushes or installs dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time


class TrialFailure(Exception):
    pass


def environment(home: Path) -> dict[str, str]:
    home.mkdir(parents=True, exist_ok=True)
    # Do not inherit personal config, credentials, PYTHONPATH or virtualenv hints.
    # PATH/base tools are deliberately retained: this is not a security sandbox.
    env = {key: os.environ[key] for key in
           ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL")
           if key in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home),
               XDG_CONFIG_HOME=str(home / "config"), XDG_CACHE_HOME=str(home / "cache"),
               TMPDIR=str(home), TMP=str(home), TEMP=str(home),
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0",
               GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.hooksPath",
               GIT_CONFIG_VALUE_0=os.devnull,
               PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
               npm_config_userconfig=os.devnull, npm_config_cache=str(home / "npm"),
               PIP_CACHE_DIR=str(home / "pip"), UV_CACHE_DIR=str(home / "uv"))
    return env


def run(command: list[str], cwd: Path, env: dict[str, str], log: Path,
        timeout: int) -> float:
    started = time.monotonic()
    with log.open("wb") as output:
        try:
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=output,
                                       stderr=subprocess.STDOUT,
                                       start_new_session=os.name == "posix")
        except OSError as error:
            raise TrialFailure("required_executable_unavailable") from error
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            process.wait()
            raise TrialFailure("command_timeout") from error
    if code:
        raise TrialFailure(f"command_exit_{code}")
    return round(time.monotonic() - started, 3)


def git(cwd: Path, env: dict[str, str], *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(cwd), *args], env=env,
                                       stderr=subprocess.DEVNULL, text=True,
                                       timeout=30).strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise TrialFailure("source_identity_or_history_unavailable") from error


def exercise(source: Path, command: list[str], output: Path, timeout: int) -> dict:
    started = time.monotonic()
    receipt = {"schema": 1, "scope": "committed_source_native_check",
               "state": "failed", "command": command, "scenarios": [],
               "limits": ["not_remote_auth", "not_model_or_IDE_trial",
                          "not_dependency_install_or_deployment", "not_a_sandbox"]}
    env = environment(output / "control-home")
    try:
        source = Path(git(source, env, "rev-parse", "--show-toplevel"))
        candidate = git(source, env, "rev-parse", "HEAD")
        tree = git(source, env, "rev-parse", "HEAD^{tree}")
        receipt.update(candidate=candidate, tree=tree)
        # Refuse a misleading pass of HEAD while the requested edits are uncommitted.
        if git(source, env, "status", "--porcelain=v1", "--untracked-files=normal"):
            raise TrialFailure("source_has_uncommitted_work")
        parent = git(source, env, "rev-parse", "--verify", "HEAD^")
        receipt["stale_base"] = parent
        for scenario in ("cold", "stale"):
            row = {"name": scenario, "state": "failed"}
            receipt["scenarios"].append(row)
            clone = output / scenario
            log = output / f"{scenario}-clone.log"
            row["log"] = str(log)
            run(["git", "clone", "--no-local", "--no-hardlinks", "--no-checkout",
                 str(source), str(clone)], output, env, log, timeout)
            git(clone, env, "checkout", "--detach", candidate if scenario == "cold" else parent)
            sentinels = {}
            if scenario == "stale":
                # Test retained local files without editing versioned product source.
                for kind in ("untracked", "ignored"):
                    name = f".contributor-trial-{kind}"
                    if git(clone, env, "ls-tree", "-r", "--name-only", candidate, "--", name):
                        raise TrialFailure("trial_sentinel_collides_with_source")
                    target = clone / name
                    target.write_bytes(b"retain unrelated local work\n")
                    sentinels[target] = target.read_bytes()
                with (clone / ".git/info/exclude").open("a", encoding="utf-8") as excluded:
                    excluded.write("\n/.contributor-trial-ignored\n")
                log = output / "stale-refresh.log"
                row["log"] = str(log)
                run(["git", "-c", "merge.autoStash=false", "merge", "--ff-only",
                     "--no-overwrite-ignore", candidate], clone, env, log, timeout)
            if git(clone, env, "rev-parse", "HEAD") != candidate:
                raise TrialFailure("candidate_mismatch")
            native_env = environment(output / f"{scenario}-home")
            # Each clone is its own primary candidate, not the caller's workspace.
            if os.environ.get("GITHUB_ACTIONS") == "true":
                native_env.update(GITHUB_ACTIONS="true", GITHUB_SHA=candidate,
                                  GITHUB_WORKSPACE=str(clone))
            log = output / f"{scenario}-native.log"
            row["log"] = str(log)
            native_started = time.monotonic()
            try:
                run(command, clone, native_env, log, timeout)
            finally:
                row["native_seconds"] = round(time.monotonic() - native_started, 3)
            if git(clone, env, "rev-parse", "HEAD") != candidate:
                raise TrialFailure("native_check_changed_candidate")
            if git(clone, env, "diff", "HEAD", "--"):
                raise TrialFailure("native_check_changed_tracked_source")
            if any(not path.exists() or path.read_bytes() != value
                   for path, value in sentinels.items()):
                raise TrialFailure("native_check_damaged_local_work")
            row.update(state="passed", retained_local_files=len(sentinels))
        if git(source, env, "rev-parse", "HEAD") != candidate:
            raise TrialFailure("source_advanced_during_trial")
        receipt["state"] = "passed"
    except (TrialFailure, OSError) as error:
        receipt["reason"] = str(error) if isinstance(error, TrialFailure) else "trial_io_failure"
        if receipt["scenarios"]:
            log = Path(receipt["scenarios"][-1]["log"])
            if log.is_file():
                with log.open("rb") as stream:
                    stream.seek(max(0, log.stat().st_size - 3000))
                    receipt["failure_excerpt"] = stream.read(3000).decode("utf-8", errors="replace")
    receipt["wall_seconds"] = round(time.monotonic() - started, 3)
    return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=".")
    parser.add_argument("--timeout", type=int, default=120, help="Seconds per command")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not 1 <= args.timeout <= 3600:
        parser.error("provide -- COMMAND [ARGS]; timeout must be 1..3600 seconds")
    # Retain logs on failure/success. Never delete user-named output directories.
    output = Path(tempfile.mkdtemp(prefix="contributor-trial-"))
    result = exercise(Path(args.source).resolve(), command, output, args.timeout)
    result["evidence_directory"] = str(output)
    (output / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
