#!/usr/bin/env python3
"""Tell an agent what to focus on in this repository, from its own history.

Read-only and host-neutral: any agent, any model, any reasoning level runs
the same command and gets the same answer.

    python3 tools/work_audit.py [--root DIR] [--commits N] [--json] [--strict]

It prints one FOCUS line (the first thing to do) and ranked findings, each
with the action that fixes it. Findings follow where agent work breaks
(references/work-health-model-2026-11.md has the sources):

- direction:    open goal; records/process loop; repeated steps; task list
                inconsistent; too much work in progress
- evidence:     unfinished code and skipped tests; tests that assert nothing;
                checks that cannot fail
- knowledge:    handoff grown into a history; instructions or handoffs that
                point at files that no longer exist
- instructions: scattered or repeated instruction files; instructions that
                keep growing; oversized required reading
- flow:         merged branches, worktrees, dated plans, scratch; large
                binaries tracked in Git
- harness:      no machine-readable list of activities agents may run
- code:         product files or functions too large to change safely

Tasks are read from .beads/issues.jsonl, backlog.json or tasks.json, the file
named in .agent/audit.json ({"tasks": "path/to/tasks.json"}), or the output of
a tracker query named there ({"tasks_command": ["bd", "list", "--json"]}). The
audit runs only known read-only tracker queries (bd list, ready, show, export);
it ignores any other command, because a repository could otherwise make this
read-only audit execute code.

Each session does the FOCUS line, so the list is worked through over time.
Cleanup commits count as records or process: when they start to dominate,
the loop finding puts product work first again.

A commit counts as product when it changes any product path. Records are
docs, handoffs, evidence and notes; process is CI, build files, agent
configuration and instruction files; tests are tests and fixtures. Override
the product paths in .agent/audit.json: {"product": ["tools/*.py"]}.
Unmatched paths are product.

Scope: a heuristic over history and text. It points at likely waste and
unfinished work; it does not judge whether a change was right.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

INSTRUCTIONS = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md")
RECORDS = re.compile(r"(^|/)(docs?|handoffs?|dev-handoff|evidence|receipts?|records?|reports?|research|references|"
                     r"notes|plans?|retros?|reviews?|adr|decisions?|status|journal|changelog)(/|$)|"
                     r"\.(md|markdown|rst|txt|adoc|org)$|(^|/)(CHANGELOG|HISTORY|NOTES)[^/]*$", re.I)
PROCESS = re.compile(r"(^|/)(\.github|\.gitlab|\.circleci|\.claude|\.cursor|\.codex|\.agents?|\.devin|\.gemini|"
                     r"\.vscode|\.idea|\.devcontainer|ci|scripts)(/|$)|(^|/)(Makefile|GNUmakefile|[^/]*\.mk|"
                     r"\.gitlab-ci\.yml|\.pre-commit-config\.yaml|Procfile|process-compose\.yaml|"
                     r"AGENTS[^/]*\.md|CLAUDE\.md|GEMINI\.md)$", re.I)
TESTS = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|testdata)(/|$)|(^|/)(test_[^/]*|[^/]*_test\.\w+|"
                   r"[^/]*\.(test|spec)\.\w+)$", re.I)
STUB = re.compile(r"\bNotImplementedError\b|unimplemented!|todo!\(|"
                  r"@unittest\.skip\(|pytest\.mark\.(skip|xfail)\b(?!if)|\b(it|describe|test)\.skip\(|@Disabled\b|"
                  r"\bt\.Skip\(")
NOTE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b|\bnot implemented\b", re.I)
UNFINISHED = re.compile(STUB.pattern + "|" + NOTE.pattern, re.I)
VENDORED = re.compile(r"(^|/)(vendor|vendored|third[_-]party|external|extern|node_modules|\.venv|venv|"
                      r"site-packages|dist|build|generated|gen|__generated__)(/|$)|\.min\.(js|css)$|_pb2\.py$", re.I)
HANDOFF = re.compile(r"(handoff|hand-off|continuation|dev-handoff)", re.I)
CODE = re.compile(r"\.(py|js|jsx|ts|tsx|go|rs|java|kt|cs|cpp|cc|c|h|hpp|rb|php|swift|scala|gd|lua|sh)$", re.I)
INSTRUCTION_FILE = re.compile(
    r"(^|/)(AGENTS[^/]*\.md|CLAUDE\.md|GEMINI\.md|CONTRIBUTOR[^/]*\.md|START-HERE\.md|[^/]*PLAYBOOK[^/]*\.md|"
    r"\.cursorrules|\.windsurfrules|copilot-instructions\.md)$|"
    r"(^|/)\.(cursor/rules|github/instructions|devin|agents|claude/(agents|commands|skills)|windsurf/rules|"
    r"clinerules|codex/prompts)/.*\.(md|mdc|txt)$", re.I)
INSTRUCTION_FILES = 8    # more instruction files than this means agents read scattered, competing text
DUPLICATES = 5           # sentences repeated across instruction files before it is a finding
READ_ONLY_TRACKERS = {"bd": {"list", "ready", "show", "export"}}
CLOSED = {"done", "closed", "completed", "complete", "resolved", "cancelled", "canceled", "wontfix", "merged",
          "duplicate", "superseded", "obsolete"}
STALE_DAYS = 14          # an in-progress claim older than this is stale
WIP_BRANCHES = 10        # unmerged local branches beyond this are work in progress nobody finishes
LARGE_FILE = 5_000_000   # bytes; tracked binaries this size slow every clone and agent search
GROWTH_WORDS = 300       # instruction words added within the commit window before it is a finding
CHECK_COMMAND = re.compile(r"\b(pytest|unittest|make (check|test|lint)|npm (run )?test|yarn test|go test|cargo test|"
                           r"ruff|flake8|mypy|eslint|tsc|phpunit|rspec|jest|vitest|godot\b.*--test)", re.I)
CANNOT_FAIL = re.compile(r"\|\|\s*(true|:|exit 0)\s*($|[;)#])", re.I)
ALWAYS_SOFT = re.compile(r"continue-on-error:\s*true|--exit-zero", re.I)
ALLOWLISTS = ("configs/allowed-activities.json", ".claude/settings.json", ".codex/rules", ".gemini/policies",
              ".cursor/sandbox-policies")
FILE_LINES = 1000        # a product file this long is hard to change safely
FUNCTION_LINES = 120     # ...and so is a function this long
ENTRY_WORDS = 1500       # always-loaded instructions an agent can still act on
LINKED_WORDS = 6000      # entry plus the documents it tells every newcomer to read
REQUIRED = re.compile(r"\b(read|start (with|from|here)|apply|follow)\b", re.I)
HANDOFF_WORDS = 800      # a current handoff, not a history
SUPPORT_SHARE = 0.5      # records + process above this share of recent commits is a loop
RECENT = 3               # ...unless one of the latest commits already changes product


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def config(root: Path) -> dict:
    try:
        data = json.loads((root / ".agent" / "audit.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def kind(path: str, product: list[str]) -> str:
    if any(fnmatch.fnmatch(path, pattern) for pattern in product):
        return "product"
    if TESTS.search(path):
        return "test"
    if PROCESS.search(path):
        return "process"
    if RECORDS.search(path) and not CODE.search(path):  # code is never a record, whatever its name
        return "records"
    return "product"


def commit_mix(root: Path, count: int, product: list[str]) -> list[dict]:
    log = git(root, "log", f"-{count}", "--no-merges", "--name-only", "--format=\x1e%h\x1f%s")
    commits = []
    for block in log.split("\x1e")[1:]:
        head, _, body = block.partition("\n")
        sha, _, subject = head.partition("\x1f")
        paths = [p for p in body.splitlines() if p.strip()]
        kinds = {kind(p, product) for p in paths}
        main = next((k for k in ("product", "test", "process", "records") if k in kinds), "records")
        commits.append({"sha": sha, "subject": subject, "kind": main, "paths": len(paths)})
    return commits


def words(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").split())
    except OSError:
        return 0


def entry_reading(root: Path) -> tuple[int, int, list[str]]:
    """Words always loaded, and words in the local documents the entry tells every agent to read."""
    loaded = [root / name for name in INSTRUCTIONS if (root / name).is_file()]
    for path in list(loaded):  # @imports load too
        for target in re.findall(r"(?m)^\s*@(\S+)", path.read_text(encoding="utf-8", errors="replace")):
            candidate = (path.parent / target).resolve()
            if candidate.is_file() and candidate not in loaded:
                loaded.append(candidate)
    linked = []
    for path in loaded:
        text = path.read_text(encoding="utf-8", errors="replace")
        required = " ".join(s for s in re.split(r"(?<=[.!?])\s+|\n\s*\n", text) if REQUIRED.search(s))
        for target in re.findall(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", required):
            candidate = (path.parent / target).resolve()
            if candidate.is_file() and candidate not in loaded and candidate not in linked:
                linked.append(candidate)
    always = sum(words(p) for p in loaded)
    return always, always + sum(words(p) for p in linked), [str(p.relative_to(root)) for p in loaded
                                                             if p.is_relative_to(root)]


def tracked(root: Path) -> list[str]:
    return [p for p in git(root, "ls-files").splitlines() if p]


def python_code_lines(text: str) -> dict[int, str] | None:
    """Python source by line with string literals (docstrings included) blanked; None if it cannot be read."""
    import io
    import tokenize
    lines = text.splitlines()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    for token in tokens:
        if token.type != tokenize.STRING:
            continue
        (row, col), (end_row, end_col) = token.start, token.end
        for number in range(row, end_row + 1):
            line = lines[number - 1]
            left = col if number == row else 0
            right = end_col if number == end_row else len(line)
            lines[number - 1] = line[:left] + " " * (right - left) + line[right:]
    return {number: line for number, line in enumerate(lines, 1)}


def interface_lines(text: str) -> set[int]:
    """Lines of Python methods whose only job is to be overridden: raising NotImplementedError there is design."""
    import ast
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return set()
    lines: set[int] = set()
    for node in statements(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lines.update(range(item.lineno, (getattr(item, "end_lineno", item.lineno) or item.lineno) + 1))
    return lines


def unfinished(root: Path, files: list[str], product: list[str]) -> list[tuple[str, int, str, str]]:
    """(path, line, text, strength): "stub" for code that cannot work yet or skipped tests, "note" for comments."""
    found = []
    for rel in files:
        if not CODE.search(rel) or kind(rel, product) not in ("product", "test") or VENDORED.search(rel):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "\x00" in text or not UNFINISHED.search(text):  # binary, or nothing to find: skip the tokenizer
            continue
        lines, without_strings = text.splitlines(), python_code_lines(text) if rel.endswith(".py") else None
        methods = interface_lines(text) if rel.endswith(".py") and "NotImplementedError" in text else set()
        for number, line in enumerate(lines, 1):
            if without_strings is not None:
                line = without_strings.get(number, "")
            code = re.sub(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", "", line)  # text inside quotes is data
            if re.search(r"UNFINISHED|STUB|NOTE|re\.compile", line):
                continue
            if STUB.search(code):
                if "NotImplementedError" in code and number in methods:
                    continue  # base-class method meant to be overridden
                found.append((rel, number, line.strip()[:100], "stub"))
            elif NOTE.search(code):
                found.append((rel, number, line.strip()[:100], "note"))
    return found


def sentences(text: str) -> list[str]:
    text = re.sub(r"`[^`]*`|\[([^\]]*)\]\([^)]*\)|[*_>#|]", lambda m: m.group(1) or " ", text)
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n|\n[-*\d]", text)
    return [" ".join(p.lower().split()) for p in parts if len(p.split()) >= 10]


def instructions(root: Path, files: list[str]) -> tuple[list[str], int, list[tuple[str, list[str]]]]:
    """Instruction files, their words, and sentences that appear in more than one of them."""
    chosen = [p for p in files if INSTRUCTION_FILE.search(p)]
    seen: dict[str, set[str]] = {}
    total = 0
    for rel in chosen:
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        total += len(text.split())
        for sentence in set(sentences(text)):
            seen.setdefault(sentence, set()).add(rel)
    repeated = [(text, sorted(where)) for text, where in seen.items() if len(where) > 1]
    return chosen, total, sorted(repeated, key=lambda r: -len(r[1]))


def statements(tree):
    """Statement nodes only: functions live in bodies, so expressions need not be walked."""
    stack = list(getattr(tree, "body", []))
    while stack:
        node = stack.pop()
        yield node
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            stack.extend(getattr(node, field, None) or [])


def size(root: Path, files: list[str], product: list[str]) -> list[tuple[str, int, str]]:
    """Product code files and Python functions too large to change safely: (path, lines, what)."""
    import ast
    found = []
    for rel in files:
        if not CODE.search(rel) or kind(rel, product) != "product" or VENDORED.search(rel):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.count("\n") + 1
        if lines > FILE_LINES:
            found.append((rel, lines, "file"))
        if rel.endswith(".py") and lines > FUNCTION_LINES:
            try:
                tree = ast.parse(text)
            except (SyntaxError, ValueError):
                continue
            for node in statements(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = (getattr(node, "end_lineno", node.lineno) or node.lineno) - node.lineno + 1
                    if length > FUNCTION_LINES:
                        found.append((f"{rel}:{node.lineno}", length, f"function {node.name}"))
    return sorted(found, key=lambda f: -f[1])


NOTES: list[str] = []


def read_only_tracker(command) -> bool:
    """A configured tracker command runs only if it is a known read-only query; repositories are untrusted."""
    if not (isinstance(command, list) and len(command) >= 2 and all(isinstance(part, str) for part in command)):
        return False
    allowed = READ_ONLY_TRACKERS.get(Path(command[0]).name if "/" not in command[0] else "")
    return bool(allowed) and command[1] in allowed


def load_tasks(root: Path, cfg: dict) -> list[dict]:
    """Tasks from a configured command or file, Beads issues.jsonl, or a backlog/tasks JSON file."""
    sources = []
    command = cfg.get("tasks_command")
    if command is not None and not read_only_tracker(command):
        NOTES.append(f"ignored tasks_command {command!r}: only read-only tracker queries run "
                     f"({', '.join(f'{k} {sorted(v)}' for k, v in READ_ONLY_TRACKERS.items())})")
    elif command:
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60, check=False)
            sources.append(result.stdout if result.returncode == 0 else "")
        except (OSError, subprocess.TimeoutExpired):
            pass
    candidates = [cfg["tasks"]] if isinstance(cfg.get("tasks"), str) else []
    candidates += [".beads/issues.jsonl", "backlog.json", "tasks.json"]
    sources += [(root / rel).read_text(encoding="utf-8", errors="replace") for rel in candidates if (root / rel).is_file()]
    for text in sources:
        try:
            data = json.loads(text)
            rows = data.get("tasks", data.get("issues", [])) if isinstance(data, dict) else data
        except ValueError:
            try:
                rows = [json.loads(line) for line in text.splitlines() if line.strip()]
            except ValueError:
                continue
        tasks = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or "id" not in row:
                continue
            raw = row.get("blocked_by") or []
            deps = [raw] if isinstance(raw, (str, int)) else list(raw) if isinstance(raw, list) else []
            dependencies = row.get("dependencies")
            for dep in dependencies if isinstance(dependencies, list) else []:
                if isinstance(dep, dict) and dep.get("type", "blocks") in ("blocks", "blocked-by", "blocked_by"):
                    deps.append(dep.get("depends_on_id") or dep.get("id"))
                elif isinstance(dep, str):
                    deps.append(dep)
            tasks.append({"id": str(row["id"]), "title": str(row.get("title", "")),
                          "status": str(row.get("status", "open")).lower(),
                          "updated": row.get("updated_at") or row.get("updated") or row.get("modified"),
                          "deps": [str(d) for d in deps if d]})
        if tasks:
            return tasks
    return []


def task_problems(tasks: list[dict], now: float | None = None) -> list[str]:
    import time
    from datetime import datetime
    now = now or time.time()
    by_id = {t["id"]: t for t in tasks}
    problems = []
    for t in tasks:
        if t["status"] in CLOSED:
            continue
        missing = [d for d in t["deps"] if d not in by_id]
        finished = [d for d in t["deps"] if d in by_id and by_id[d]["status"] in CLOSED]
        if missing:
            problems.append(f"{t['id']} depends on missing {', '.join(missing)} (fix: remove "
                            f"{', '.join(missing)} from its blockers)")
        if t["status"] == "blocked" and t["deps"] and len(finished) == len(t["deps"]):
            problems.append(f"{t['id']} is blocked only by finished {', '.join(finished)} (fix: set it to ready)")
        if t["status"] in ("in_progress", "in-progress", "doing", "active") and isinstance(t["updated"], str):
            try:
                age = (now - datetime.fromisoformat(t["updated"].replace("Z", "+00:00")).timestamp()) / 86400
            except ValueError:
                age = 0
            if age > STALE_DAYS:
                problems.append(f"{t['id']} claimed in progress {age:.0f} days ago with no update (fix: set it "
                                "back to open unless you finish it now)")
    titles: dict[str, list[str]] = {}
    for t in tasks:
        if t["status"] not in CLOSED and t["title"]:
            titles.setdefault(" ".join(re.findall(r"[a-z0-9]+", t["title"].lower())), []).append(t["id"])
    problems += [f"duplicate open tasks {', '.join(ids)} (fix: keep {ids[0]}, close "
                 f"{', '.join(ids[1:])} as duplicate)" for ids in titles.values() if len(ids) > 1]
    return problems


def vacuous_tests(root: Path, files: list[str]) -> list[str]:
    """Python test functions that assert nothing (directly or through a helper in the same file)."""
    import ast
    found = []
    for rel in files:
        if not (rel.endswith(".py") and TESTS.search(rel)) or VENDORED.search(rel):
            continue
        try:
            tree = ast.parse((root / rel).read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            continue
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

        def exercises(node):
            # A test that calls code can fail: a validator that raises, a smoke run. Only a test that
            # calls nothing and asserts nothing cannot fail.
            for child in ast.walk(node):
                if isinstance(child, (ast.Assert, ast.Raise)):
                    return True
                if isinstance(child, ast.Call):
                    func = child.func
                    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                    if name not in ("print", "len", "str", "repr", "dict", "list", "set", "tuple"):
                        return True
            return False
        found += [f"{rel}:{f.lineno} {f.name}" for f in functions if f.name.startswith("test") and not exercises(f)]
    return found


def cannot_fail(root: Path, files: list[str]) -> list[str]:
    """CI and build steps written so that a failure still passes."""
    found = []
    for rel in files:
        if not re.search(r"(^|/)(\.github/workflows/[^/]+\.ya?ml|\.gitlab-ci\.yml|Makefile|GNUmakefile|[^/]+\.mk)$", rel):
            continue
        try:
            lines = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        found += [f"{rel}:{n} {line.strip()[:70]}" for n, line in enumerate(lines, 1)
                  if not line.lstrip().startswith("#") and (ALWAYS_SOFT.search(line) or (
                      CANNOT_FAIL.search(line) and CHECK_COMMAND.search(line)))]
    return found


def broken_references(root: Path, files: list[str]) -> list[str]:
    """Local links in instruction and handoff files whose target no longer exists."""
    found = []
    for rel in files:
        if not (INSTRUCTION_FILE.search(rel) or HANDOFF.search(rel)) or not rel.endswith((".md", ".mdc")):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for target in re.findall(r"\]\(([^)#\s:]+)(?:#[^)]*)?\)", text):
            from urllib.parse import unquote
            path = unquote(target)
            base = root if path.startswith("/") else (root / rel).parent
            if not base.joinpath(path.lstrip("/")).exists():
                found.append(f"{rel} -> {target}")
    return found


def instruction_growth(root: Path, chosen: list[str], count: int) -> tuple[int, int]:
    """Instruction words now and at the start of the commit window."""
    old_ref = git(root, "rev-list", "--max-count=1", f"--skip={count}", "HEAD").strip()
    if not old_ref:
        return 0, 0
    old_files = [p for p in git(root, "ls-tree", "-r", "--name-only", old_ref).splitlines() if INSTRUCTION_FILE.search(p)]
    before = sum(len(git(root, "show", f"{old_ref}:{p}").split()) for p in old_files)
    return before, sum(words(root / p) for p in chosen)


def work_in_progress(root: Path) -> tuple[int, int]:
    """Unmerged local branches and registered worktrees."""
    base = next((b for b in ("origin/HEAD", "origin/main", "main", "origin/master", "master")
                 if git(root, "rev-parse", "--verify", "--quiet", b).strip()), None)
    unmerged = [b for b in git(root, "branch", "--format=%(refname:short)", "--no-merged", base).splitlines()
                if b.strip()] if base else []
    worktrees = git(root, "worktree", "list", "--porcelain").count("\nworktree ") + 0
    return len(unmerged), worktrees


def large_files(root: Path, files: list[str]) -> list[tuple[str, int]]:
    found = []
    for rel in files:
        try:
            size_bytes = (root / rel).stat().st_size
        except OSError:
            continue
        if size_bytes > LARGE_FILE:
            found.append((rel, size_bytes))
    return sorted(found, key=lambda f: -f[1])


def handoff_files(files: list[str]) -> list[str]:
    """Handoff documents, the one to keep first (a README, else the shortest path). Code is never a handoff."""
    chosen = [p for p in files if HANDOFF.search(p) and re.search(r"\.(md|markdown|txt|rst|adoc)$", p, re.I)]
    return sorted(chosen, key=lambda p: (not p.lower().endswith("readme.md"), len(p), p))


def handoffs(root: Path, files: list[str]) -> tuple[int, int]:
    chosen = handoff_files(files)
    return len(chosen), sum(words(root / p) for p in chosen)


def goal_open(root: Path) -> str | None:
    """The recorded goal, unless the finish gate's last verdict on this same goal was "met"."""
    path, status = root / ".agent" / "goal.json", root / ".agent" / "goal-status.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    goal = data.get("goal") if isinstance(data, dict) and isinstance(data.get("goal"), str) else None
    try:
        verdict = json.loads(status.read_text(encoding="utf-8"))
        if (verdict.get("goal") == goal and verdict.get("met") is True
                and status.stat().st_mtime >= path.stat().st_mtime):
            return None
    except (OSError, ValueError, AttributeError):
        pass
    return goal


def hygiene(root: Path) -> list[str]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from check_hygiene import findings  # same directory, optional
        return findings(root, None)
    except Exception:  # hygiene is advisory here; a failure must not hide the rest
        return []


def finding(kind: str, problem: str, action: str) -> dict:
    return {"kind": kind, "area": AREA[kind], "problem": problem, "action": action}


def direction(ctx: dict) -> list[dict]:
    """Is the next piece of work the one that closes the user's gap?"""
    found, commits = [], ctx["commits"]
    goal = goal_open(ctx["root"])
    if goal:
        found.append(finding("goal", f"open goal record: {goal!r}",
                             "Finish this goal first: make each check in .agent/goal.json pass "
                             "(python3 tools/finish_check.py shows what is unmet)."))
    if commits:
        support = sum(c["kind"] in ("records", "process") for c in commits)
        share = support / len(commits)
        recent_product = any(c["kind"] == "product" for c in commits[:RECENT])
        if share > SUPPORT_SHARE and not recent_product:
            examples = "; ".join(c["subject"][:60] for c in commits if c["kind"] in ("records", "process"))[:240]
            found.append(finding("loop", f"{support}/{len(commits)} recent commits changed only records or process "
                                         f"({share:.0%}), e.g. {examples}",
                                 "Make the next commit change product behaviour and prove it with a check. "
                                 "Add a record only when someone will act on it; replace the old one."))
        opening = lambda c: " ".join(c["subject"].lower().split()[:3])
        openings = Counter(opening(c) for c in commits)
        latest = {opening(c) for c in commits[:RECENT]}  # history an agent cannot change is not a finding
        repeated = [(text, n) for text, n in openings.most_common(3)
                    if n >= 3 and len(text.split()) == 3 and text in latest]
        if repeated:
            found.append(finding("repeat", "repeating commit subjects: "
                                 + ", ".join(f"'{t}' x{n}" for t, n in repeated),
                                 "Stop repeating the step. Name what each repeat failed to achieve and change the "
                                 "approach, or mark the item blocked with the reason."))
    tasks = task_problems(load_tasks(ctx["root"], ctx["cfg"]))
    if tasks:
        found.append(finding("tasks", f"{len(tasks)} task-list inconsistencies: " + "; ".join(tasks[:6]),
                             "Reconcile the task list first, in one commit, by making each fix listed: "
                             + "; ".join(tasks[:6]) + ". These are bookkeeping corrections, not owner decisions; "
                             "the task list is how the next agent chooses work."))
    return found


def evidence(ctx: dict) -> list[dict]:
    """Do the checks prove what they claim?"""
    found, gaps, notes = [], ctx["gaps"], ctx["notes"]
    if gaps:
        top = Counter(rel for rel, *_ in gaps).most_common(5)
        first = gaps[0]
        found.append(finding("unfinished", f"{len(gaps)} stubs or skipped tests in code; most in "
                             + ", ".join(f"{rel} ({n})" for rel, n in top),
                             f"Finish or delete the incomplete code, starting with {first[0]}:{first[1]} "
                             f"({first[2]}). A skipped test is unfinished work, not a pass."))
    if notes:
        top = Counter(rel for rel, *_ in notes).most_common(5)
        found.append(finding("todo-notes", f"{len(notes)} TODO/FIXME notes in code; most in "
                             + ", ".join(f"{rel} ({n})" for rel, n in top),
                             "When a task touches one of these, finish the note or turn it into a task in the "
                             "task list and delete it. Notes alone are not a reason to start work."))
    rules = ctx["rules"]
    empty = [e for e in vacuous_tests(ctx["root"], ctx["files"]) if not ignored(rules, "vacuous-tests", e.split(":")[0])]
    if empty:
        found.append(finding("vacuous-tests", f"{len(empty)} tests call no code and assert nothing, e.g. "
                             + ", ".join(empty[:3]),
                             "Give each of these tests a call and an assertion that fail when the behaviour "
                             "breaks, or delete it. A test that cannot fail proves nothing."))
    soft = [c for c in cannot_fail(ctx["root"], ctx["files"]) if not ignored(rules, "cannot-fail", c.split(":")[0])]
    if soft:
        found.append(finding("cannot-fail", f"{len(soft)} build or CI checks cannot fail, e.g. " + "; ".join(soft[:3]),
                             "Let these checks fail when they find a problem, or delete them. Report a known "
                             "failure as a failure, not as a pass."))
    return found


def knowledge(ctx: dict) -> list[dict]:
    """Is what the next agent will read current and complete?"""
    found = []
    count_handoff, handoff_words = handoffs(ctx["root"], ctx["files"])
    if count_handoff > 1 or handoff_words > HANDOFF_WORDS:
        keep, *others = handoff_files(ctx["files"])
        extra = f" and delete {', '.join(others[:8])}{' ...' if len(others) > 8 else ''}" if others else ""
        found.append(finding("handoff", f"{count_handoff} handoff/continuation files, {handoff_words} words",
                             f"Rewrite {keep} as the one current handoff under {HANDOFF_WORDS} words (goal, last "
                             f"proven state, next action){extra}; history is in Git. Replace that file at each "
                             "checkpoint instead of adding a new one."))
    broken = [b for b in broken_references(ctx["root"], ctx["files"])
              if not ignored(ctx["rules"], "stale-references", b.split(" -> ")[0])]
    if broken:
        found.append(finding("stale-references", f"{len(broken)} links in instructions or handoffs point at "
                             "missing files, e.g. " + "; ".join(broken[:3]),
                             "Fix or delete each broken link. An instruction that points at nothing is stale "
                             "knowledge the next agent will act on."))
    return found


def guidance(ctx: dict) -> list[dict]:
    """Can an agent find and act on its instructions?"""
    found, root = [], ctx["root"]
    chosen, instruction_words, repeated = instructions(root, ctx["files"])
    if len(chosen) > INSTRUCTION_FILES or len(repeated) >= DUPLICATES:
        example = f"; e.g. repeated in {', '.join(repeated[0][1][:3])}" if repeated else ""
        source = next((p for p in chosen if p == "AGENTS.md"), "AGENTS.md")
        copies = sorted({p for _, where in repeated for p in where if p != source})
        edits = f" Delete the repeated text from {', '.join(copies[:6])}{' ...' if len(copies) > 6 else ''}" \
                f" and keep it once in {source}." if copies else ""
        pointer = " Make CLAUDE.md a pointer: @AGENTS.md." if "CLAUDE.md" in copies else ""
        found.append(finding("instructions", f"{len(chosen)} agent instruction files ({instruction_words} words), "
                             f"{len(repeated)} sentences repeated across them{example}",
                             f"Keep one source of instructions ({source} and the documents it links).{edits}"
                             f"{pointer} This moves text without changing any rule, so it needs no owner "
                             "decision; changing what a rule says still does. Where two files disagree, keep "
                             "the newer decision and delete the other."))
    before, after = instruction_growth(root, chosen, ctx["count"])
    if before and after - before > GROWTH_WORDS:
        found.append(finding("instruction-growth", f"instruction files grew from {before} to {after} words "
                             f"within the last {ctx['count']} commits",
                             "Replace added prose with a check, a tool or a deletion. Repeated failures need "
                             "enforcement or better placement, not more sentences."))
    always, linked, loaded = entry_reading(root)
    if always > ENTRY_WORDS or linked > LINKED_WORDS:
        found.append(finding("entry", f"entry reading is {always} words always loaded ({', '.join(loaded)}) and "
                             f"{linked} words with the documents it tells every agent to read",
                             "Shorten the entry to the loop and the hard limits; move the rest behind on-demand "
                             "links. Delete rules that no check or trial supports."))
    return found


def flow(ctx: dict) -> list[dict]:
    """Is finished work closed and are resources released?"""
    found, root = [], ctx["root"]
    unmerged, worktrees = work_in_progress(root)
    if unmerged > WIP_BRANCHES or worktrees > WIP_BRANCHES:
        found.append(finding("wip", f"{unmerged} unmerged branches and {worktrees} extra worktrees",
                             "Finish, merge or close open work before starting more: for each branch, merge it, "
                             "record why it waits in the task list, or delete it once its commits are kept."))
    heavy = large_files(root, ctx["files"])
    if heavy:
        found.append(finding("large-files", f"{len(heavy)} tracked files over {LARGE_FILE // 1_000_000} MB, e.g. "
                             + ", ".join(f"{p} ({b // 1_000_000} MB)" for p, b in heavy[:3]),
                             "Move generated or binary artefacts out of Git (release assets, LFS or a data store) "
                             "and ignore them."))
    found += [finding("hygiene", line, "Clean it up: delete merged branches and finished worktrees through Git; "
                                       "keep one current plan or handoff.") for line in hygiene(root)]
    return found


def harness(ctx: dict) -> list[dict]:
    """Does the host know what agents may do without asking?"""
    if any((ctx["root"] / path).exists() for path in ALLOWLISTS):
        return []
    return [finding("allowlist", "no machine-readable list of activities agents may run",
                    "Propose, for the owner to approve, the local commands agents may run without asking "
                    "(for example configs/allowed-activities.json rendered by agentic-engineering's "
                    "tools/allowlist.py). Permissions are the owner's decision; do not grant them yourself.")]


def code(ctx: dict) -> list[dict]:
    """Can the next change be made safely?"""
    large = [z for z in size(ctx["root"], ctx["files"], ctx["product"]) if not ignored(ctx["rules"], "size", z[0].split(":")[0])]
    if not large:
        return []
    return [finding("size", f"{len(large)} oversized product files or functions; largest "
                    + ", ".join(f"{where} ({lines} lines, {what})" for where, lines, what in large[:4]),
                    "When a task changes one of these, split the part you change by responsibility and keep its "
                    "tests passing. Do not refactor code no task touches.")]


AREAS = (direction, evidence, knowledge, guidance, flow, harness, code)
ORDER = ["goal", "loop", "repeat", "tasks", "unfinished", "vacuous-tests", "cannot-fail", "handoff",
         "stale-references", "instructions", "instruction-growth", "entry", "wip", "hygiene", "large-files",
         "allowlist", "todo-notes", "size"]
NEVER_FOCUS = {"todo-notes", "size"}
# Per-file judgements that can be wrong in a given repository. Direction, knowledge and flow findings are
# counted facts about history and state; an ignore rule cannot silence them.
IGNORABLE = {"unfinished", "todo-notes", "vacuous-tests", "cannot-fail", "stale-references", "size", "large-files",
             "allowlist"}  # advisory: acted on when a task touches the code, never a task by themselves
AREA = {kind: area for area, kinds in (
    ("direction", ("goal", "loop", "repeat", "tasks")),
    ("evidence", ("unfinished", "vacuous-tests", "cannot-fail", "todo-notes")),
    ("knowledge", ("handoff", "stale-references")), ("instructions", ("instructions", "instruction-growth", "entry")),
    ("flow", ("wip", "hygiene", "large-files")), ("harness", ("allowlist",)), ("code", ("size",))) for kind in kinds}


def choose_focus(found: list[dict], gaps: list) -> str:
    kinds = [f["kind"] for f in found]
    if gaps and kinds[:1] in (["loop"], ["repeat"]):
        # A loop with known unfinished code: name the target, so any model can act on it.
        rel, number, text, _ = gaps[0]
        return (f"This is the next task: finish {rel}:{number} ({text}) and prove it with a check, in this "
                "session. If a records-only task blocks it, close that in one short commit, then continue here; "
                "the records task does not end the session.")
    if found and found[0]["kind"] not in NEVER_FOCUS:
        return found[0]["action"]
    return ("No waste signal found. Take the highest-priority ready task, change product behaviour, and prove it "
            "with a check.")


def ignore_rules(cfg: dict) -> list[dict]:
    """Verified false positives recorded in .agent/audit.json: {"kind", "path" (glob), "reason"}."""
    rules = []
    for rule in cfg.get("ignore", []) if isinstance(cfg.get("ignore"), list) else []:
        if (isinstance(rule, dict) and rule.get("kind") in IGNORABLE and isinstance(rule.get("path", "*"), str)
                and len(re.findall(r"[A-Za-z]{2,}", str(rule.get("reason", "")))) >= 3):
            rules.append(rule)
        else:
            NOTES.append(f"ignored invalid ignore rule {rule!r}: it needs a reason of three words and one of "
                         f"these kinds: {', '.join(sorted(IGNORABLE))}")
    return rules


def ignored(rules: list[dict], kind_name: str, path: str) -> bool:
    return any(r["kind"] == kind_name and fnmatch.fnmatch(path, r.get("path", "*")) for r in rules)


def audit(root: Path, count: int) -> dict:
    NOTES.clear()
    cfg = config(root)
    product = [p for p in cfg.get("product", []) if isinstance(p, str)]
    rules = ignore_rules(cfg)
    files = tracked(root)
    marks = [m for m in unfinished(root, files, product)
             if not ignored(rules, "unfinished" if m[3] == "stub" else "todo-notes", m[0])]
    ctx = {"root": root, "cfg": cfg, "product": product, "count": count, "files": files, "rules": rules,
           "commits": commit_mix(root, count, product),
           "gaps": [m for m in marks if m[3] == "stub"], "notes": [m for m in marks if m[3] == "note"]}
    found = [f for area in AREAS for f in area(ctx) if not ignored(rules, f["kind"], "*")]
    found.sort(key=lambda f: ORDER.index(f["kind"]))
    if rules:
        NOTES.append(f"{len(rules)} verified false positives skipped (.agent/audit.json ignore)")
    mix = Counter(c["kind"] for c in ctx["commits"])
    return {"root": str(root), "commits": len(ctx["commits"]), "mix": dict(mix),
            "focus": choose_focus(found, ctx["gaps"]), "findings": found, "notes": list(NOTES)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--commits", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any finding is present")
    args = parser.parse_args(argv)
    report = audit(Path(args.root).resolve(), args.commits)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        mix = ", ".join(f"{k} {v}" for k, v in sorted(report["mix"].items())) or "no history"
        print(f"work-audit: last {report['commits']} commits: {mix}")
        print(f"FOCUS: {report['focus']}")
        for note in report["notes"]:
            print(f"note: {note}")
        for number, finding in enumerate(report["findings"], 1):
            print(f"{number}. [{finding['area']}/{finding['kind']}] {finding['problem']}\n   -> {finding['action']}")
    return 1 if args.strict and report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
