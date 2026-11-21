#!/usr/bin/env python3
"""Refuse tracked files that must never be published in this repository.

Checks every file tracked by Git: font binaries and source maps (fonts are
licensed for use, not redistribution), personal e-mail addresses, absolute
local paths and access tokens. Prints one line per finding, exits 1 if any.
"""
from __future__ import annotations

import re
import subprocess
import sys

FORBIDDEN_EXT = (".woff", ".woff2", ".ttf", ".otf", ".eot", ".map")
PATTERNS = {
    "e-mail address": re.compile(r"[\w.+-]+@(?!users\.noreply\.github\.com)[A-Za-z][\w-]*(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"),
    "absolute local path": re.compile(r"(?<![\w.])/(?:srv|home|Users|root)/[\w.-]+"),
    "access token": re.compile(r"\b(?:gh[opsur]_|github[_]pat_|sk-[A-Za-z0-9]{8}|xox[bp]-|AKIA[0-9A-Z]{12})"),
    "source map reference": re.compile(r"sourceMappingURL="),
}
ALLOWED_EMAILS = frozenset({"hello@ghost.org"})
PLACEHOLDER_EMAIL_DIRS = ("locales/",)  # upstream translations: sample addresses only


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True, text=True).stdout
    return [f for f in out.split("\0") if f]


def main() -> int:
    findings: list[str] = []
    for path in tracked():
        if path.lower().endswith(FORBIDDEN_EXT):
            findings.append(f"{path}: forbidden file type")
            continue
        if path.startswith(".github/scripts/"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        for no, line in enumerate(text.splitlines(), 1):
            for label, rx in PATTERNS.items():
                for m in rx.finditer(line):
                    if label == "e-mail address" and (
                        m.group(0) in ALLOWED_EMAILS or path.startswith(PLACEHOLDER_EMAIL_DIRS)
                    ):
                        continue
                    findings.append(f"{path}:{no}: {label}: {m.group(0)[:60]}")
    for f in findings:
        print(f)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
