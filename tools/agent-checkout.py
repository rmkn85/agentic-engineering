#!/usr/bin/env python3
"""Inspect one owned checkout; optionally fetch or clean-fast-forward it.

No task store, dependency installer, credential discovery, branch switching,
commit, push, force update, or deployment. Python standard library + Git only.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit


class Blocked(Exception):
    pass


def repository_id(url: str) -> str:
    """Normalize a GitHub HTTPS/SSH URL without returning credentials."""
    value = url.strip()
    scp = re.fullmatch(r"git@github\.com:([^?#]+)", value, re.I)
    if scp:
        path = scp.group(1)
    else:
        parsed = urlsplit(value)
        if parsed.hostname != "github.com" or parsed.scheme not in ("https", "ssh"):
            raise Blocked("remote_identity_unrecognized")
        if parsed.query or parsed.fragment or parsed.password:
            raise Blocked("remote_identity_unrecognized")
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git").rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", path):
        raise Blocked("remote_identity_unrecognized")
    return path.lower()


def git(root: Path, *args: str) -> str:
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            timeout=30, env=environment, check=False,
        )
    except FileNotFoundError as error:
        raise Blocked("git_unavailable") from error
    except subprocess.TimeoutExpired as error:
        raise Blocked("git_timeout") from error
    if result.returncode:
        # Raw Git diagnostics may contain credential-bearing remote URLs.
        raise Blocked("git_" + args[0].replace("-", "_") + "_failed")
    return result.stdout.strip()


def unchanged(root: Path, head: str) -> None:
    if git(root, "rev-parse", "HEAD") != head:
        raise Blocked("checkout_changed_during_inspection")
    if git(root, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise Blocked("working_tree_not_clean")


def inspect(args: argparse.Namespace, receipt: dict) -> None:
    root = Path(args.path).resolve()
    root = Path(git(root, "rev-parse", "--show-toplevel"))
    receipt["repository"] = args.expect.lower()
    for mode in ([], ["--push"]):
        urls = git(root, "remote", "get-url", "--all", *mode, args.remote).splitlines()
        if not urls or any(repository_id(url) != args.expect.lower() for url in urls):
            raise Blocked("wrong_repository_or_push_destination")
    for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        path = Path(git(root, "rev-parse", "--git-path", marker))
        if (path if path.is_absolute() else root / path).exists():
            raise Blocked("git_operation_in_progress")
    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "branch", "--show-current")
    receipt.update(head=head, branch=branch or None)
    unchanged(root, head)
    if args.revision:
        if head != args.revision.lower():
            raise Blocked("candidate_revision_mismatch")
        receipt.update(state="exact_candidate", freshness="not_asserted", mutated=False)
        return
    if branch != args.branch:
        raise Blocked("wrong_or_detached_branch")
    ref = "refs/remotes/" + args.remote + "/" + args.branch
    if args.fetch or args.ff_only:
        git(root, "fetch", "--no-tags", args.remote,
            "refs/heads/" + args.branch + ":" + ref)
        receipt["freshness"] = "fetched_this_invocation"
    else:
        receipt["freshness"] = "cached_remote_ref_only"
    target = git(root, "rev-parse", "--verify", ref)
    ahead, behind = map(int, git(root, "rev-list", "--left-right", "--count", head + "..." + target).split())
    receipt.update(upstream=target, ahead=ahead, behind=behind, mutated=False)
    if ahead:
        raise Blocked("diverged" if behind else "unpublished_local_commits")
    if behind and args.ff_only:
        unchanged(root, head)
        git(root, "merge", "--ff-only", "--no-edit", target)
        receipt.update(head=git(root, "rev-parse", "HEAD"), behind=0, mutated=True)
        if receipt["head"] != target:
            raise Blocked("checkout_changed_during_fast_forward")
    elif behind:
        raise Blocked("behind_remote")
    if not (args.fetch or args.ff_only):
        raise Blocked("remote_freshness_unverified")
    unchanged(root, receipt["head"])
    receipt["state"] = "current_clean_checkout"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=".")
    parser.add_argument("--expect", required=True, help="Expected GitHub owner/repository")
    parser.add_argument("--remote", default="origin")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--branch", help="Explicitly authorized current branch; never switched")
    mode.add_argument("--revision", help="Exact 40-character candidate SHA for read-only CI inspection")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--fetch", action="store_true")
    action.add_argument("--ff-only", action="store_true", help="Fetch, then fast-forward only a clean owned checkout")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.expect):
        parser.error("--expect must be owner/repository")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", args.remote):
        parser.error("unsupported remote name")
    if args.revision and (not re.fullmatch(r"[0-9a-fA-F]{40}", args.revision) or args.fetch or args.ff_only):
        parser.error("--revision requires an exact SHA and forbids fetch/mutation")
    if args.branch and (args.branch.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]*", args.branch)):
        parser.error("unsupported branch name")
    receipt = {"schema": 1, "state": "blocked", "scope": "checkout_only"}
    try:
        inspect(args, receipt)
        code = 0
    except (Blocked, OSError, ValueError) as error:
        receipt.update(state="blocked", reason=str(error) if isinstance(error, Blocked) else "inspection_failed")
        receipt["next"] = "Preserve work; inspect the named failure and repository entry guide. Do not force, reset, switch, or bypass permissions."
        code = 3
    print(json.dumps(receipt, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
