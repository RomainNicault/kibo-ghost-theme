#!/usr/bin/env python3
"""Refuse tracked files that must never be published in this repository.

Checks every file tracked by Git: font binaries, source maps and Python
bytecode (fonts are licensed for use, not redistribution), any other binary
file and any non UTF-8 file, personal e-mail addresses, absolute local paths,
access tokens and secrets in their raw form (Ghost Admin API key, Ghost session
cookie, private key block, 1Password service account token), in every tracked
file, these scripts included. Prints one line per finding, exits 1 if any.
"""
from __future__ import annotations

import re
import subprocess
import sys

FORBIDDEN_EXT = (".woff", ".woff2", ".ttf", ".otf", ".eot", ".map", ".pyc")
PATTERNS = {
    "e-mail address": re.compile(r"[\w.+-]+@(?!users\.noreply\.github\.com)[A-Za-z][\w-]*(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"),
    "absolute local path": re.compile(r"(?<![\w.])/(?:srv|home|Users|root)/[\w.-]+"),
    "access token": re.compile(r"\b(?:gh[opsur]_|github[_]pat_|sk-[A-Za-z0-9]{8}|xox[bp]-|AKIA[0-9A-Z]{12})"),
    "source map reference": re.compile(r"sourceMapping[U]RL="),
    "Ghost Admin API key": re.compile(r"\b[0-9a-f]{24}:[0-9a-f]{64}\b"),
    "Ghost session cookie": re.compile(r"ghost-admin-api-sessio[n]|\bs%3[A][\w-]{20,}\.[\w%/+-]{20,}"),
    "private key block": re.compile(r"-{5}BEGIN (?:[A-Z]+ )*PRIVATE KE[Y]"),
    "1Password token": re.compile(r"\bop[s]_[A-Za-z0-9_-]{20,}"),
}
ALLOWED_EMAILS = frozenset({"hello@ghost.org"})
PLACEHOLDER_EMAIL_DIRS = ("locales/",)  # upstream translations: sample addresses only


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True, text=True).stdout
    return [f for f in out.split("\0") if f]


def line_findings(path: str, line: str, placeholders: bool = True) -> list[str]:
    """Generic findings in one line of a tracked file; `placeholders=False` drops the locales exemption."""
    found = []
    for label, rx in PATTERNS.items():
        if label == "e-mail address" and "@" not in line:
            continue
        for m in rx.finditer(line):
            if label == "e-mail address" and (
                m.group(0) in ALLOWED_EMAILS or (placeholders and path.startswith(PLACEHOLDER_EMAIL_DIRS))
            ):
                continue
            found.append(f"{label}: {m.group(0)[:60]}")
    return found


def main() -> int:
    findings: list[str] = []
    for path in tracked():
        if path.lower().endswith(FORBIDDEN_EXT):
            findings.append(f"{path}: forbidden file type")
            continue
        with open(path, "rb") as fh:
            data = fh.read()
        if b"\0" in data:
            findings.append(f"{path}: binary file")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(f"{path}: non UTF-8 file")
            continue
        for no, line in enumerate(text.splitlines(), 1):
            findings += [f"{path}:{no}: {f}" for f in line_findings(path, line)]
    for f in findings:
        print(f)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
