#!/usr/bin/env python3
"""Gate of the promote workflow: decide whether a transit commit may be published.

Usage: promote_gate.py <sha> <base>, run in a clone that already holds both commits;
`base` is the commit of main being checked out.
Reads the whole tree of <sha>, never executes it. Refuses any entry that is not
a regular file on the theme allowlist, any binary or non UTF-8 file, any file
over the size limit, and any path or line matching the generic checks of
check_tree.py (on lines not already in the same file on main, the
checked-out base) or the PRIVATE_LEXICON secret (one case-insensitive regular
expression, matched on raw, NFKC and typography-normalised text, on the same
text with CSS and JavaScript escapes, HTML entities and tags decoded, and on the
whole file with white space removed). `.github/` is not promoted: the workflow
keeps the one on `main`.

Public logs must not reveal what was refused: the gate prints only
"gate passed" or "gate failed", and any error counts as a failure. For local
diagnosis only, set PROMOTE_EXPLAIN=1 to print the reasons to stderr; the
workflow never sets it.
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_tree import FORBIDDEN_EXT, line_findings  # noqa: E402

SHA_RE = re.compile(r"[0-9a-f]{40}")
MAX_BLOB = 2_000_000
ALLOWED_PATHS = re.compile(
    r"\.gitignore|LICENSE|README\.md|package\.json|gulpfile\.js|[a-z0-9-]+\.hbs"
    r"|partials/(?:[a-z0-9-]+/)?[a-z0-9-]+\.hbs|locales/[A-Za-z-]+\.json"
    r"|assets/(?:built|css)/[a-z0-9-]+\.(?:css|js)|assets/js/(?:lib/)?[a-z0-9.-]+\.js"
)
TYPOGRAPHY = str.maketrans({
    "\u2019": "'", "\u2018": "'", "\u02bc": "'", "\u00a0": " ", "\u202f": " ", "\u2009": " ",
    "\u2007": " ", "\u2002": " ", "\u2003": " ", "\u2010": "-", "\u2011": "-", "\u2012": "-",
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00ad": "", "\u200b": "", "\u2060": "", "\ufeff": "",
})
SEPARATORS = str.maketrans({"-": " ", "_": " "})
JS_ESCAPE = re.compile(r"\\u\{([0-9a-fA-F]{1,6})\}|\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})")
CSS_ESCAPE = re.compile(r"\\([0-9a-fA-F]{1,6})[ \t\r\n\f]?|\\(.)", re.S)
TAG = re.compile(r"<[^<>]*>")


def _char(code: str) -> str:
    try:
        return chr(int(code, 16))
    except (ValueError, OverflowError):
        return ""


def decoded(text: str) -> str:
    """Text with JavaScript and CSS escapes, HTML entities and tags undone: catches an encoded term."""
    text = JS_ESCAPE.sub(lambda m: _char(m.group(1) or m.group(2) or m.group(3)), text)
    text = CSS_ESCAPE.sub(lambda m: _char(m.group(1)) if m.group(1) else m.group(2), text)
    return TAG.sub("", html.unescape(text))


def git(*args: str) -> bytes:
    res = subprocess.run(["git", *args], capture_output=True, check=True, timeout=120,
                         env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"})
    return res.stdout


def private(lexicon: re.Pattern[str], text: str) -> bool:
    for variant in (text, decoded(text)):
        plain = unicodedata.normalize("NFKC", variant.translate(TYPOGRAPHY)).casefold()
        if any(lexicon.search(t) for t in (variant, plain, plain.translate(SEPARATORS))):
            return True
    return False


def joined(text: str) -> str:
    """Whole file with every run of white space removed: catches a term split across lines."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text.translate(TYPOGRAPHY)).casefold())


BASE = ""


def refused(sha: str, lexicon: re.Pattern[str], reasons: list[str] | None = None) -> bool:
    """True if anything in the tree of `sha` must not be published."""
    out = reasons if reasons is not None else []

    def no(reason: str) -> bool:
        out.append(reason)
        return True

    if git("cat-file", "-t", sha).strip() != b"commit":
        return no(f"{sha}: not a commit")
    entries = [e for e in git("ls-tree", "-r", "-z", "--full-tree", sha).split(b"\0") if e]
    if not entries:
        return no("empty tree")
    refused_any = False
    for entry in entries:
        meta, path_b = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        path = path_b.decode("utf-8")
        if path == ".github" or path.startswith(".github/"):
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            refused_any |= no(f"{path}: not a regular file")
            continue
        if not ALLOWED_PATHS.fullmatch(path):
            refused_any |= no(f"{path}: path not allowed")
            continue
        if path.lower().endswith(FORBIDDEN_EXT):
            refused_any |= no(f"{path}: forbidden file type")
            continue
        if private(lexicon, path):
            refused_any |= no(f"{path}: private term in name")
            continue
        if int(git("cat-file", "-s", oid)) > MAX_BLOB:
            refused_any |= no(f"{path}: too large")
            continue
        data = git("cat-file", "blob", oid)
        if b"\0" in data:
            refused_any |= no(f"{path}: binary")
            continue
        text = data.decode("utf-8")
        if lexicon.search(joined(text)) or lexicon.search(joined(decoded(text))):
            refused_any |= no(f"{path}: private term (joined)")
        known = base_lines(path)
        for no_, line in enumerate(text.splitlines(), 1):
            if private(lexicon, line):
                refused_any |= no(f"{path}:{no_}: private term")
            elif line not in known:
                for f in line_findings(path, line, placeholders=False):
                    refused_any |= no(f"{path}:{no_}: {f}")
    return refused_any


def base_lines(path: str) -> set[str]:
    """Lines of the same file on base: already public, exempt from the generic checks only."""
    res = subprocess.run(["git", "cat-file", "blob", f"{BASE}:{path}"], capture_output=True, check=False, timeout=120)
    return set(res.stdout.decode("utf-8", "replace").splitlines()) if res.returncode == 0 else set()


def main(argv: list[str]) -> int:
    try:
        global BASE
        sha, BASE = (argv[1], argv[2]) if len(argv) == 3 else ("", "")
        source = os.environ.get("PRIVATE_LEXICON", "").strip()
        if not SHA_RE.fullmatch(sha) or not SHA_RE.fullmatch(BASE) or not source:
            raise ValueError
        lexicon = re.compile(source, re.IGNORECASE)
        reasons: list[str] = []
        failed = refused(sha, lexicon, reasons)
        if failed and os.environ.get("PROMOTE_EXPLAIN") == "1":
            print("\n".join(reasons) or "refused without reason", file=sys.stderr)
    except BaseException as exc:  # noqa: BLE001 - any error is a refusal, never a detail in the logs
        failed = True
        if os.environ.get("PROMOTE_EXPLAIN") == "1":
            print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
    print("gate failed" if failed else "gate passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
