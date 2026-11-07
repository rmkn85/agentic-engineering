#!/usr/bin/env python3
"""Refuse shell commands that no agent task may run without the owner.

Rules every adopting workspace had restated in prose:

- desktop: never drive or capture the user's desktop. Input injection and
  screen capture are allowed only on an agent-owned isolated display
  (a command run under xvfb-run that does not point DISPLAY elsewhere).
- force-push / remote deletion: never rewrite or delete published history.
- discard: never throw away uncommitted or unmerged work (reset --hard,
  clean -f, forced checkout/switch, restoring a whole directory, stash
  drop/clear, branch -D, worktree remove --force, deleting .git).
  Allowed inside a temporary directory, where clones are disposable.

Quoted text, commit messages and heredoc bodies are data, not commands.
Command substitutions, sh -c strings, eval, xargs, find -exec and common
wrappers (sudo, env, timeout, nice, ...) are inspected.

This is a guard, not a proof: it catches the spellings its tests cover.
A refusal is not a dead end: ask the owner, or use a non-destructive route.

Use as a Claude Code PreToolUse hook (--hook reads the event on stdin; exit 2
blocks the call and tells the agent why) or directly: --command "...".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import PurePosixPath

OPERATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", ";;"}
INPUT_TOOLS = {"xdotool", "ydotool", "xte", "wtype", "dotool", "cliclick", "evemu-play", "evemu-event"}
CAPTURE_TOOLS = {"scrot", "gnome-screenshot", "grim", "maim", "spectacle", "flameshot", "screencapture",
                 "xwd", "ksnip", "shutter"}
GRAB = re.compile(r"\b(x11grab|gdigrab|avfoundation|kmsgrab|pipewiregrab|ximagesrc|pipewiresrc|"
                  r"ScreenCast|Screenshot)\b")
DESKTOP_LIBS = re.compile(r"\b(pyautogui|pynput|ImageGrab|mss|robotjs|nut-js|Xlib\.ext\.xtest)\b")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
# wrapper -> options that take a value
WRAPPERS = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-r", "-t", "-U"}, "doas": {"-u", "-C"},
    "env": {"-u", "-C", "-S"}, "nohup": set(), "time": {"-f", "-o"}, "nice": {"-n"},
    "ionice": {"-c", "-n", "-p"}, "command": set(), "exec": {"-a"}, "stdbuf": {"-i", "-o", "-e"},
    "timeout": {"-s", "-k", "--signal", "--kill-after"}, "xargs": {"-I", "-n", "-P", "-d", "-L", "-s", "-E", "-a"},
    "setsid": set(), "chrt": set(), "taskset": set(),
}
TIMED = {"timeout", "taskset", "chrt"}  # first positional is a duration / mask / priority
XVFB_OPTS = {"-s", "-n", "-f", "-e", "-w", "-p", "--server-args", "--server-num", "--auth-file",
             "--error-file", "--wait"}
GIT_GLOBAL_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
TEMP_ROOTS = tuple({os.path.realpath(p) for p in (tempfile.gettempdir(), "/tmp", "/var/tmp",
                                                   os.environ.get("TMPDIR", "/tmp")) if p})


def split_heredocs(command: str) -> tuple[str, list[str]]:
    """Drop heredoc bodies (data), except bodies fed to a shell, which are returned to be checked."""
    out, executed, delimiter, body, to_shell = [], [], None, [], False
    for line in command.split("\n"):
        if delimiter is not None:
            if line.strip() in (delimiter, delimiter + ")"):
                if to_shell:
                    executed.append("\n".join(body))
                delimiter, body = None, []
                if line.strip().endswith(")"):
                    out.append(")")
            else:
                body.append(line)
            continue
        out.append(line)
        match = re.search(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", line)
        if match:
            delimiter = match.group(2)
            head = re.split(r"[;&|(]", line[:match.start()])[-1].split()
            to_shell = bool(head) and PurePosixPath(head[0]).name in SHELLS and "-c" not in head
    return "\n".join(out), executed


def substitutions(command: str) -> list[str]:
    """Command substitutions that the shell would run: outside single quotes only."""
    found, quote, index = [], None, 0
    while index < len(command):
        char = command[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if quote == "'":
            quote = None if char == "'" else quote
        elif char == "'" and quote is None:
            quote = "'"
        elif char == '"':
            quote = None if quote == '"' else '"'
        elif char == "`":
            close = command.find("`", index + 1)
            if close > index:
                found.append(command[index + 1:close])
                index = close
        elif command.startswith("$(", index):
            depth, cursor = 1, index + 2
            while cursor < len(command) and depth:
                depth += {"(": 1, ")": -1}.get(command[cursor], 0)
                cursor += 1
            found.append(command[index + 2:cursor - 1])
            index = cursor - 1
        index += 1
    return [inner for inner in found if inner.strip()]


def unquoted_newlines_to_separators(command: str) -> str:
    out, quote, escaped = [], None, False
    for char in command:
        if escaped:
            escaped = False
        elif char == "\\" and quote != "'":
            escaped = True
        elif quote:
            quote = None if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char == "\n":
            char = ";"
        out.append(char)
    return "".join(out)


def tokens(command: str) -> list[str]:
    command = unquoted_newlines_to_separators(split_heredocs(command)[0])
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError:  # unbalanced quotes: fall back to a rough split
        return re.split(r"\s+", command)


def simple_commands(words: list[str]) -> list[tuple[list[str], str]]:
    """Commands with the operator that precedes each one ("|" means it reads a pipe)."""
    result, current, before = [], [], ""
    for word in words:
        if word in OPERATORS or re.fullmatch(r"[;&|()]+", word):
            if current:
                result.append((current, before))
            current, before = [], word
        else:
            current.append(word)
    if current:
        result.append((current, before))
    return result


def under_temp(path: str | None) -> bool:
    if not path:
        return False
    real = os.path.realpath(path)
    return any(real == root or real.startswith(root + os.sep) for root in TEMP_ROOTS)


def unwrap(words: list[str], ctx: dict) -> list[str]:
    """Drop variable assignments and wrapper commands with their options."""
    while words:
        head = words[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", head):
            if head.startswith("DISPLAY="):
                ctx["isolated"] = False
            words = words[1:]
            continue
        name = PurePosixPath(head).name
        if name not in WRAPPERS:
            break
        valued, words = WRAPPERS[name], words[1:]
        while words and (words[0].startswith("-") or (name == "env" and "=" in words[0])):
            option = words[0]
            if option.startswith("DISPLAY="):
                ctx["isolated"] = False
            words = words[2:] if option in valued else words[1:]
            if option == "--":
                break
        if name in TIMED and words:
            words = words[1:]
    return words


def cluster(arg: str, letter: str) -> bool:
    return arg.startswith("-") and not arg.startswith("--") and letter in arg[1:]


def broad_path(arg: str) -> bool:
    return arg in (".", "./", ":/", ":/*", "*", "..") or arg.endswith("/") or arg.endswith("/*")


def git_violation(args: list[str], ctx: dict) -> tuple[str, bool] | None:
    """Return (reason, discards_local_work) or None."""
    workdir = ctx.get("cwd")
    while args and args[0].startswith("-"):
        if args[0] == "-c" and len(args) > 1 and args[1].lower().startswith("alias."):
            return "hidden command: a git -c alias can run anything; run the command directly", False
        option = args[0].split("=", 1)[0]
        if option == "-C" and len(args) > 1:
            workdir = os.path.join(workdir or ".", args[1])
        args = args[2:] if option in GIT_GLOBAL_OPTS and "=" not in args[0] else args[1:]
    ctx["git_dir"] = workdir
    if not args:
        return None
    sub, rest = args[0], args[1:]
    if sub == "push":
        if any(a in ("--force", "--mirror") or a.startswith(("--force-with-lease", "--force-if-includes"))
               or cluster(a, "f") or a.startswith("+") for a in rest):
            return "force-push: rewriting published history needs the owner; push a new branch instead", False
        if any(a in ("--delete", "--prune") or cluster(a, "d") or (a.startswith(":") and len(a) > 1)
               for a in rest):
            return "remote deletion: deleting a published branch or tag needs the owner", False
    elif sub == "reset" and "--hard" in rest:
        return "discard: reset --hard drops uncommitted work; use git stash or a new branch", True
    elif sub == "clean" and any(cluster(a, "f") or a == "--force" for a in rest):
        return "discard: clean -f deletes untracked files; list them with git clean -n and ask", True
    elif sub == "checkout" and (any(a in ("-f", "--force") or cluster(a, "f") for a in rest)
                                or ("--" in rest and any(broad_path(a) for a in rest[rest.index("--") + 1:]))
                                or (rest and broad_path(rest[-1]))):
        return "discard: forced or whole-directory checkout drops uncommitted work; stash it first", True
    elif sub in ("switch", "checkout") and any(a in ("-C", "-B", "--force-create") for a in rest):
        return "discard: resetting an existing branch can drop its unmerged commits; create a new branch", True
    elif sub == "update-ref" and any(a in ("-d", "--delete") for a in rest):
        return "discard: deleting a ref can drop unmerged commits; use git branch -d", True
    elif sub == "switch" and any(a in ("-f", "--force", "--discard-changes") or cluster(a, "f") for a in rest):
        return "discard: switch --discard-changes drops uncommitted work; stash it first", True
    elif sub == "restore":
        staged_only = ("--staged" in rest or cluster("".join(a for a in rest if not a.startswith("--")), "S")) \
            and "--worktree" not in rest and not any(cluster(a, "W") for a in rest)
        paths = [a for a in rest if not a.startswith("-")]
        if not staged_only and any(broad_path(a) for a in paths):
            return "discard: restoring a whole directory drops uncommitted work; stash it first", True
    elif sub == "stash" and rest[:1] in (["drop"], ["clear"]):
        return "discard: dropping a stash loses work; ask the owner", True
    elif sub == "branch":
        forced_delete = any(a == "-D" or cluster(a, "D") for a in rest) or (
            any(a in ("-d", "--delete") or cluster(a, "d") for a in rest)
            and any(a in ("-f", "--force") or cluster(a, "f") for a in rest))
        if forced_delete:
            return "discard: forced branch deletion loses unmerged commits; use branch -d", True
    elif sub == "worktree" and rest[:1] == ["remove"] and any(a in ("-f", "--force") or cluster(a, "f")
                                                              for a in rest[1:]):
        return "discard: worktree remove --force drops its uncommitted work; harvest it first", True
    return None


def check(words: list[str], ctx: dict, depth: int = 0) -> str | None:
    if depth > 8 or not words:
        return None
    words = unwrap(words, ctx)
    if not words:
        return None
    name = PurePosixPath(words[0]).name
    args = words[1:]
    if name == "cd":
        target = args[0] if args else "~"
        if "$" in target or target == "-" or ctx.get("cwd") is None and not target.startswith(("/", "~")):
            ctx["cwd"] = None  # unknown directory: never treated as disposable
        else:
            ctx["cwd"] = os.path.join(ctx.get("cwd") or "/", os.path.expanduser(target))
        return None
    if name in ("export", "declare", "typeset", "local", "readonly") and any(
            a.startswith("DISPLAY=") for a in args):
        ctx["isolated"] = False
        return None
    if name == "gh" and args[:1] == ["api"] and re.search(r"(-X|--method)\s*=?\s*DELETE", " ".join(args), re.I) \
            and "git/refs" in " ".join(args):
        return "remote deletion: deleting a published branch or tag needs the owner"
    if name == "xvfb-run":
        inner = list(args)
        while inner and inner[0].startswith("-"):
            inner = inner[2:] if inner[0].split("=", 1)[0] in XVFB_OPTS and "=" not in inner[0] else inner[1:]
        return check(inner, dict(ctx, isolated=True), depth + 1)
    if name in SHELLS:
        for index, arg in enumerate(args):
            if cluster(arg, "c") and index + 1 < len(args):
                return violation(args[index + 1], ctx, depth + 1)
        return None
    if name == "eval":
        return violation(" ".join(args), ctx, depth + 1)
    if name == "find":
        for index, arg in enumerate(args):
            if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                inner = []
                for item in args[index + 1:]:
                    if item in (";", "+", "\\;"):
                        break
                    inner.append(item)
                found = check(inner, ctx, depth + 1)
                if found:
                    return found
        return None
    if name == "git":
        found = git_violation(args, ctx)
        if found:
            reason, discards = found
            if discards and under_temp(ctx.get("git_dir") or ctx.get("cwd")):
                return None  # disposable clone in a temporary directory
            return reason
        return None
    if name == "rm" and any(cluster(a, "r") or cluster(a, "R") or a == "--recursive" for a in args) and any(
            PurePosixPath(a.rstrip("/")).name == ".git" for a in args if not a.startswith("-")):
        if not under_temp(ctx.get("cwd")):
            return "discard: deleting .git destroys all local history; ask the owner"
    if not ctx.get("isolated"):
        joined = " ".join(words)
        if name in INPUT_TOOLS:
            return f"desktop: {name} injects input into the user's session; use an isolated display (xvfb-run)"
        if name in CAPTURE_TOOLS or (name == "import" and "root" in args):
            return f"desktop: {name} captures the user's screen; capture only an agent-owned display"
        if name in ("ffmpeg", "gst-launch-1.0", "gst-launch", "gdbus", "dbus-send", "busctl") and GRAB.search(joined):
            return f"desktop: {name} records the user's session; use an isolated display"
        if name == "osascript" and re.search(r"keystroke|key code|click", joined):
            return "desktop: osascript UI scripting drives the user's desktop"
        if re.match(r"(python[0-9.]*|node|ruby|perl)$", name) and DESKTOP_LIBS.search(joined):
            return f"desktop: {name} loads a desktop automation or capture library"
    return None


def violation(command: str, ctx: dict | None = None, depth: int = 0) -> str | None:
    ctx = dict(ctx or {})
    ctx.setdefault("isolated", False)
    if depth > 8:
        return None
    text, executed = split_heredocs(command)
    for inner in substitutions(text) + executed:
        found = violation(inner, ctx, depth + 1)
        if found:
            return found
    previous: list[str] = []
    for words, before in simple_commands(tokens(command)):
        head = PurePosixPath(unwrap(list(words), dict(ctx))[0]).name if unwrap(list(words), dict(ctx)) else ""
        if before == "|" and head in SHELLS and not any(cluster(a, "c") for a in words[1:]):
            if previous[:1] and PurePosixPath(previous[0]).name in ("echo", "printf"):
                found = violation(" ".join(previous[1:]), ctx, depth + 1)
                if found:
                    return found
            else:
                return "hidden command: piping generated text into a shell cannot be checked; run it directly"
        found = check(words, ctx, depth)
        if found:
            return found
        previous = words
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--command")
    group.add_argument("--hook", action="store_true", help="read a Claude Code PreToolUse event on stdin")
    parser.add_argument("--cwd", help="directory the command runs in (default: current)")
    args = parser.parse_args(argv)
    command, cwd = args.command, args.cwd
    if args.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return 0
        if not isinstance(event, dict) or event.get("tool_name") != "Bash":
            return 0
        tool_input = event.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        if not isinstance(command, str):
            return 0
        cwd = event.get("cwd") if isinstance(event.get("cwd"), str) else None
    found = violation(command or "", {"cwd": cwd or os.getcwd()})
    if found:
        print(f"guard: refused ({found}). Ask the owner if this is really required.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
