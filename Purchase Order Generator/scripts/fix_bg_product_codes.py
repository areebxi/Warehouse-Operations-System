#!/usr/bin/env python3
"""
Set BTC Product Code from Gender Apparel when it contains 'bg-'.

Rule: BTC Product Code = text after the first 'bg-' in Gender Apparel (case-insensitive).
Example: BG-BG125J -> BG125J, BG-China-Bag -> China-Bag
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import app_paths  # noqa: F401

from app_paths import data_path

DEFAULT_PATH = data_path("Custom Label Database.csv")


def extract_code(gender_apparel: str) -> str | None:
    value = gender_apparel or ""
    idx = value.casefold().find("bg-")
    if idx < 0:
        return None
    return value[idx + 3 :].strip()


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                rows = list(reader)
            return fieldnames, rows, encoding
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix BTC Product Code from Gender Apparel (bg- rows).")
    parser.add_argument("--csv", type=Path, default=DEFAULT_PATH, help="Custom Label Database.csv path")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not write")
    parser.add_argument("--no-backup", action="store_true", help="Skip .bak backup before overwrite")
    args = parser.parse_args()

    path = args.csv
    if not path.is_file():
        print(f"Error: not found: {path}")
        return 1

    fieldnames, rows, encoding = load_csv(path)
    if "Gender Apparel" not in fieldnames or "BTC Product Code" not in fieldnames:
        print("Error: CSV must have 'Gender Apparel' and 'BTC Product Code' columns")
        return 1

    updated = 0
    unchanged = 0
    for row in rows:
        code = extract_code(row.get("Gender Apparel", ""))
        if code is None:
            continue
        if row.get("BTC Product Code", "").strip() == code:
            unchanged += 1
            continue
        row["BTC Product Code"] = code
        updated += 1

    print(f"File: {path}")
    print(f"Rows with bg- in Gender Apparel: {updated + unchanged}")
    print(f"BTC Product Code updated: {updated}")
    print(f"Already correct: {unchanged}")

    if args.dry_run:
        print("\nDry run — no files changed.")
        return 0

    if not args.no_backup:
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        print(f"\nBackup: {backup}")

    with open(path, "w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
