"""Minimal reader for Paradox (Clausewitz) script files.

It does not build a full syntax tree. It finds top-level entries and keeps their exact text, so a
tool can copy an object out of a game file, rename keys inside it, and write it back unchanged
everywhere else. Standard library only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def read_text(path: Path) -> str:
    """Game files are UTF-8, some with a byte-order mark, a few in Windows-1252."""
    data = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


@dataclass
class Entry:
    key: str          # the name on the left of '='
    text: str         # exact text of the whole entry, key included
    body: str         # text between the outer braces ('' for a scalar)
    is_block: bool
    path: Path | None = None


def _skip_ws_and_comments(s: str, i: int) -> int:
    n = len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c == "#":
            j = s.find("\n", i)
            i = n if j < 0 else j + 1
        else:
            break
    return i


def _read_token(s: str, i: int) -> tuple[str, int]:
    n = len(s)
    if s[i] == '"':
        j = i + 1
        while j < n and s[j] != '"':
            j += 2 if s[j] == "\\" else 1
        return s[i:j + 1], j + 1
    j = i
    while j < n and s[j] not in " \t\r\n={}#<>!":
        j += 1
    if j == i:          # a lone operator or brace
        j = i + 1
    return s[i:j], j


def match_brace(s: str, i: int) -> int:
    """s[i] is '{'. Return the index just past its matching '}'."""
    depth = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "#":
            j = s.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            j = i + 1
            while j < n and s[j] != '"':
                j += 2 if s[j] == "\\" else 1
            i = j + 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced braces")


def entries(text: str, path: Path | None = None) -> list[Entry]:
    """Top-level `key = value` and `key = { ... }` entries, in file order."""
    out: list[Entry] = []
    i, n = 0, len(text)
    while True:
        i = _skip_ws_and_comments(text, i)
        if i >= n:
            break
        start = i
        key, i = _read_token(text, i)
        i = _skip_ws_and_comments(text, i)
        if i >= n or text[i] not in "=<>":
            continue                      # stray token; ignore
        while i < n and text[i] in "=<>!":
            i += 1
        i = _skip_ws_and_comments(text, i)
        if i >= n:
            break
        if text[i] == "{":
            end = match_brace(text, i)
            out.append(Entry(key.strip('"'), text[start:end], text[i + 1:end - 1], True, path))
            i = end
        else:
            _, end = _read_token(text, i)
            out.append(Entry(key.strip('"'), text[start:end], "", False, path))
            i = end
    return out


def load_dir(folder: Path, pattern: str = "*.txt") -> list[Entry]:
    out: list[Entry] = []
    for f in sorted(Path(folder).glob(pattern)):
        try:
            out.extend(entries(read_text(f), f))
        except ValueError as exc:
            print(f"WARN {f}: {exc}")
    return out


def field(body: str, name: str) -> str | None:
    """Value of the first top-level `name = x` inside a block body. Blocks come back with braces."""
    for e in entries(body):
        if e.key == name:
            return e.text.split("=", 1)[1].strip() if not e.is_block else "{" + e.body + "}"
    return None


def fields(body: str, name: str) -> list[Entry]:
    return [e for e in entries(body) if e.key == name]


def str_list(block: str | None) -> list[str]:
    """`{ "a" b }` -> ['a', 'b']"""
    if not block:
        return []
    return re.findall(r'"([^"]+)"|([^\s{}"]+)', block.strip("{}")) and [
        a or b for a, b in re.findall(r'"([^"]+)"|([^\s{}"]+)', block.strip("{}"))
    ]


def check_balanced(text: str) -> bool:
    """True when every brace closes, ignoring comments and strings."""
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if c == '"':
            j = text.find('"', i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0
