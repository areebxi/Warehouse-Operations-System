#!/usr/bin/env python3
"""Remove rows from Custom Label Database.csv by BTC Product Code."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import app_paths  # noqa: F401

from app_paths import data_path

DEFAULT_PATH = data_path("Custom Label Database.csv")

# Codes to remove (exact match on BTC Product Code)
REMOVE_CODES = frozenset({
    "C2200",
    "TPC001",
    "JH001",
    "JH01J",
    "TD02B",
    "JC003",
    "C2400",
    "2400",
    "AA77",
    "C800T",
    "JC03J",
    "SH5891",
})


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove rows with listed BTC Product Codes.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    path = args.csv
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    kept = [r for r in rows if (r.get("BTC Product Code") or "").strip() not in REMOVE_CODES]
    removed = len(rows) - len(kept)

    print(f"File: {path}")
    print(f"Remove codes: {', '.join(sorted(REMOVE_CODES))}")
    print(f"Removed: {removed}")
    print(f"Remaining: {len(kept)}")

    if args.dry_run:
        print("\nDry run — no files changed.")
        return 0

    if not args.no_backup:
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        print(f"\nBackup: {backup}")

    try:
        out = path
        with open(out, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(kept)
        print(f"Updated: {out}")
    except PermissionError:
        fallback = path.with_name(path.stem + "_cleaned" + path.suffix)
        with open(fallback, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(kept)
        print(f"\nCould not write {path} (file may be open).")
        print(f"Wrote: {fallback}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
