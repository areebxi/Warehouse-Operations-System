"""Report source files over 200 physical lines. Exit 1 if any found.

Usage:
  python scripts/check_line_limit.py              # scan warehouse root
  python scripts/check_line_limit.py path [path…] # check given paths only
"""

from __future__ import annotations

import sys
from pathlib import Path

LIMIT = 200
SOURCE_SUFFIXES = {".py", ".ps1", ".bat", ".js"}
EXEMPT_PARTS = frozenset({"Versions", "backups", "__pycache__"})


def warehouse_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_exempt(path: Path) -> bool:
    if any(part in EXEMPT_PARTS for part in path.parts):
        return True
    # Historical archive under Custom Label Database/docs/archive/**
    parts = path.parts
    if "docs" in parts and "archive" in parts:
        return True
    return False


def line_count(path: Path) -> int:
    with path.open("rb") as f:
        return sum(1 for _ in f)


def iter_sources(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    for root in roots:
        root = root.resolve()
        if root.is_file():
            if root.suffix.lower() in SOURCE_SUFFIXES and not is_exempt(root):
                found.append(root)
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if is_exempt(p):
                continue
            found.append(p)
    return found


def offenders(paths: list[Path]) -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    for p in paths:
        n = line_count(p)
        if n > LIMIT:
            out.append((n, p))
    out.sort(key=lambda t: (-t[0], str(t[1]).lower()))
    return out


def main(argv: list[str]) -> int:
    root = warehouse_root()
    targets = [Path(a) for a in argv] if argv else [root]
    bad = offenders(iter_sources(targets))
    for n, p in bad:
        try:
            rel = p.resolve().relative_to(root)
        except ValueError:
            rel = p
        print(f"{n}\t{rel.as_posix()}")
    return 1 if bad else 0


def _self_check() -> None:
    here = Path(__file__).resolve()
    n = line_count(here)
    assert n <= LIMIT, f"check_line_limit.py itself is {n} lines (limit {LIMIT})"
    assert offenders([here]) == []
    # Tiny oversize fixture via a temp path is unnecessary; empty list is the pass case.
    assert iter_sources([here]) == [here]


if __name__ == "__main__":
    _self_check()
    raise SystemExit(main(sys.argv[1:]))
