#!/usr/bin/env python3
"""Refuse shell commands that no agent task may run without the owner.

Rules every adopting workspace had restated in prose:

- desktop: never drive or capture the user's desktop. Input injection and
  screen capture are allowed only inside an agent-owned isolated display
  (a command run under xvfb-run).
- force-push: never rewrite published history.
- discard: never throw away uncommitted or unmerged work (reset --hard,
  clean -f, checkout/restore of the whole tree, stash drop/clear, branch -D).

A refusal is not a dead end: ask the owner, or use a non-destructive route
(a new branch, git stash, git branch -d, an isolated display).

Use as a Claude Code PreToolUse hook (--hook reads the event on stdin; exit 2
blocks the call and tells the agent why) or directly: --command "...".
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys

SEPARATORS = re.compile(r"&&|\|\||[;|\n&]|\$\(|`|\(|\)")
WRAPPERS = {"sudo", "env", "nohup", "time", "nice", "command", "exec", "timeout", "stdbuf"}
INPUT_TOOLS = {"xdotool", "ydotool", "xte", "wtype", "dotool", "cliclick", "evemu-play", "evemu-event"}
CAPTURE_TOOLS = {"scrot", "gnome-screenshot", "grim", "maim", "spectacle", "flameshot", "screencapture",
                 "xwd", "ksnip", "shutter"}
GRAB_FORMATS = re.compile(r"\b(x11grab|gdigrab|avfoundation|kmsgrab|pipewiregrab)\b")


def segments(command: str) -> list[list[str]]:
    result = []
    for part in SEPARATORS.split(command):
        try:
            words = shlex.split(part, posix=True)
        except ValueError:
            words = part.split()
        while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in WRAPPERS):
            words = words[1:]
            # skip option values of simple wrappers such as `timeout 5`
            while words and re.fullmatch(r"-\S+|\d+[smhd]?", words[0]):
                words = words[1:]
        if words:
            words[0] = words[0].rsplit("/", 1)[-1]
            result.append(words)
    return result


def git_violation(words: list[str]) -> str | None:
    args = words[1:]
    while args and args[0].startswith("-"):  # git -C dir, -c k=v
        args = args[2:] if args[0] in ("-C", "-c") else args[1:]
    if not args:
        return None
    sub, rest = args[0], args[1:]
    if sub == "push" and (any(a in ("-f", "--force") or a.startswith("--force-with-lease")
                              or a.startswith("--force-if-includes") or a == "--mirror" for a in rest)
                          or any(a.startswith("+") for a in rest)):
        return "force-push: rewriting published history needs the owner; push a new branch instead"
    if sub == "reset" and "--hard" in rest:
        return "discard: reset --hard drops uncommitted work; use git stash or a new branch"
    if sub == "clean" and any(re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", a) or a == "--force" for a in rest):
        return "discard: clean -f deletes untracked files; list them with git clean -n and ask"
    whole_tree = any(a in (".", ":/", "*", ":/*") for a in rest)
    staged_only = "--staged" in rest and "--worktree" not in rest and "-W" not in rest
    if whole_tree and (sub == "checkout" or (sub == "restore" and not staged_only)):
        return "discard: restoring the whole tree drops uncommitted work; stash it first"
    if sub == "stash" and rest[:1] in (["drop"], ["clear"]):
        return "discard: dropping a stash loses work; ask the owner"
    if sub == "branch" and any(a in ("-D",) or (a.startswith("-") and "D" in a and not a.startswith("--"))
                               for a in rest):
        return "discard: branch -D deletes unmerged commits; use branch -d"
    return None


def violation(command: str) -> str | None:
    for words in segments(command):
        name = words[0]
        if name == "xvfb-run":
            continue  # everything in this segment runs on an agent-owned display
        if name in ("bash", "sh", "zsh", "dash") and "-c" in words[1:-1]:
            found = violation(words[words.index("-c") + 1])
            if found:
                return found
            continue
        if name == "git":
            found = git_violation(words)
            if found:
                return found
        if name in INPUT_TOOLS:
            return f"desktop: {name} injects input into the user's session; use an isolated display (xvfb-run)"
        if name in CAPTURE_TOOLS or (name == "import" and "root" in words):
            return f"desktop: {name} captures the user's screen; capture only an agent-owned display"
        if name == "ffmpeg" and GRAB_FORMATS.search(" ".join(words)):
            return "desktop: ffmpeg screen grab records the user's session; use an isolated display"
        if name == "osascript" and re.search(r"keystroke|key code|click", " ".join(words)):
            return "desktop: osascript UI scripting drives the user's desktop"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--command")
    group.add_argument("--hook", action="store_true", help="read a Claude Code PreToolUse event on stdin")
    args = parser.parse_args(argv)
    command = args.command
    if args.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError:
            return 0
        if event.get("tool_name") != "Bash":
            return 0
        command = str((event.get("tool_input") or {}).get("command", ""))
    found = violation(command or "")
    if found:
        print(f"guard: refused ({found}). Ask the owner if this is really required.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
