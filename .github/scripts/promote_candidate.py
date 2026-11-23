#!/usr/bin/env python3
"""Decide what the scheduled promote workflow does with the transit candidate.

Usage: promote_candidate.py <base>, run in a clone of main (full history) that
already holds the transit refs fetched under refs/transit/: `main`,
`publication` (the candidate, set by the agent after the served page was
checked) and `deployed/*` (one tag per theme sent to the site).
`base` is the commit of main being checked out.

Prints `action=<promote|skip|refuse>` and `sha=<candidate>` for GITHUB_OUTPUT,
nothing else. Reasons go to stderr only with PROMOTE_EXPLAIN=1; the workflow
never sets it. Any error counts as a refusal.

- skip: no candidate, candidate already promoted (a commit of main carries its
  `Transit-Commit` trailer), candidate tree equal to main outside `.github/`,
  or a promotion merged less than 24 hours ago.
- refuse: candidate not reachable from the transit `main`, candidate without a
  `deployed/*` tag, or a commit of main since the last promotion that touches
  files outside `.github/` without a `Transit-Commit` trailer (report it to the
  transit first).
- promote: everything else; the gate still runs after this decision.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time

SHA_RE = re.compile(r"[0-9a-f]{40}")
TRAILER = re.compile(r"^Transit-Commit: ([0-9a-f]{40})$", re.M)
MIN_INTERVAL = 24 * 3600


def git(*args: str, check: bool = True) -> str:
    res = subprocess.run(["git", *args], capture_output=True, text=True, check=check, timeout=120,
                         env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"})
    return res.stdout.strip()


def tree_without_github(rev: str) -> list[str]:
    entries = git("ls-tree", "-r", "-z", "--full-tree", rev).split("\0")
    return sorted(e for e in entries if e and not e.split("\t", 1)[1].startswith(".github/"))


def decide(base: str, now: float, reasons: list[str]) -> tuple[str, str]:
    sha = git("rev-parse", "-q", "--verify", "refs/transit/publication^{commit}", check=False)
    if not SHA_RE.fullmatch(sha):
        reasons.append("no candidate")
        return "skip", ""
    log = git("log", "--format=%H%x00%ct%x00%B%x01", base).split("\x01")
    promoted: list[tuple[str, int]] = []
    since_last: list[str] = []
    for record in log:
        if not record.strip():
            continue
        commit, ctime, body = record.strip("\n").split("\0", 2)
        found = TRAILER.findall(body)
        if found:
            promoted.append((found[-1], int(ctime)))
        elif not promoted:
            since_last.append(commit)
    if sha in {s for s, _ in promoted}:
        reasons.append("candidate already promoted")
        return "skip", sha
    if tree_without_github(sha) == tree_without_github(base):
        reasons.append("candidate tree equal to main")
        return "skip", sha
    if subprocess.run(["git", "merge-base", "--is-ancestor", sha, "refs/transit/main"],
                      capture_output=True, timeout=120).returncode:
        reasons.append("candidate not on transit main")
        return "refuse", sha
    tags = git("for-each-ref", "--points-at", sha, "--format=%(refname)", "refs/transit/deployed/")
    if not tags:
        reasons.append("candidate never deployed")
        return "refuse", sha
    for commit in since_last:
        files = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", "-m", commit).splitlines()
        if any(f and not f.startswith(".github/") for f in files):
            reasons.append(f"{commit}: change on main outside .github without Transit-Commit")
            return "refuse", sha
    if promoted and now - promoted[0][1] < MIN_INTERVAL:
        reasons.append("last promotion less than 24 hours ago")
        return "skip", sha
    return "promote", sha


def main(argv: list[str]) -> int:
    reasons: list[str] = []
    try:
        if len(argv) != 2 or not SHA_RE.fullmatch(argv[1]):
            raise ValueError("usage: promote_candidate.py <base>")
        action, sha = decide(argv[1], float(os.environ.get("PROMOTE_NOW") or time.time()), reasons)
    except BaseException as exc:  # noqa: BLE001 - any error is a refusal, never a detail in the logs
        action, sha = "refuse", ""
        reasons.append(f"error: {type(exc).__name__}: {exc}")
    if os.environ.get("PROMOTE_EXPLAIN") == "1" and reasons:
        print("\n".join(reasons), file=sys.stderr)
    print(f"action={action}")
    print(f"sha={sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
