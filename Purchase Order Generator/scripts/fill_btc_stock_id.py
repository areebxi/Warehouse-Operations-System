#!/usr/bin/env python3
"""
Fill BTC Stock ID in Custom Label Database.csv from ProductExport.csv.

Match keys (all required):
  - Custom Label Database.BTC Product Code  ->  ProductExport.SPC
  - Custom Label Database.Colour Name       ->  ProductExport.Colour Name
  - Custom Label Database.Size (mapped)     ->  ProductExport.Size

Value copied: ProductExport.UID -> Custom Label Database.BTC Stock ID

Existing BTC Stock ID values are overwritten when a match is found.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from collections import Counter
from pathlib import Path

import app_paths  # noqa: F401

from app_paths import data_path

# Custom Label full name -> ProductExport abbreviation
SIZE_TO_PRODUCT_EXPORT: dict[str, str] = {
    "small": "S",
    "medium": "M",
    "large": "L",
    "extra large": "XL",
    "extra-large": "XL",
    "x-large": "XL",
    "x large": "XL",
    "xs": "XS",
    "2xl": "2XL",
    "3xl": "3XL",
    "4xl": "4XL",
    "5xl": "5XL",
    "one size": "O/S",
    "o/s": "O/S",
    "standard size": "O/S",
}

# Youth SPCs: Custom Label age label -> ProductExport letter size (18000B, 18500B, SF500B)
YOUTH_LETTER_SPCS = frozenset(x.casefold() for x in ("18000B", "18500B", "SF500B"))
YOUTH_AGE_TO_LETTER_SIZE: dict[str, str] = {
    "3-4 years": "XS",
    "4 years": "XS",
    "4-5 years": "XS",
    "5-6 years": "S",
    "5 years": "S",
    "7-8 years": "S",
    "9-11 years": "M",
    "12-14 years": "L",
    "12-13 years": "L",
    "14-15 years": "XL",
    "1-2 years": "XS",
    "2 years": "XS",
    "2-3 years": "XS",
    "3 years": "XS",
    "0-3 months": "XS",
    "3-6 months": "XS",
    "6-12 months": "XS",
    "12-18 months": "XS",
    "18-24 months": "XS",
}

# Baby/toddler SPCs: age label -> ProductExport month/year code (BZ02, BZ10)
BZ_MONTH_SPCS = frozenset(x.casefold() for x in ("BZ02", "BZ10"))
BZ_AGE_TO_MONTH_CODE: dict[str, str] = {
    "0-3 months": "0-3",
    "3-6 months": "3-6",
    "6-12 months": "6-12",
    "12-18 months": "12-18",
    "18-24 months": "18-24",
    "2-3 years": "2-3",
}

# Custom Label colour name -> ProductExport Colour Name (lookup only; CSV unchanged)
COLOUR_ALIASES: dict[str, str] = {
    "navy": "Navy Blue",
    "royal blue": "Royal",
    "dark royal": "Royal",
    "sports grey": "Sport Grey",
    "dark heather grey": "Dark Heather",
    "classic pink": "Classic Pink/ Light Grey",
    "fuchsia": "Fuchsia/Graphite",
    "lime": "Lime/graphite",
    "purple": "Purple/Light Grey",
    "classic pink-graphite": "Graphite",
    "fuchsia-graphite": "Graphite",
    "light purple": "Purple",
    "yellow": "Yellow/Graphite Grey",
    "surf blue": "Surf Blue/ Graphite Grey",
    "surf blue-graphite grey": "Graphite",
    "natural-black": "Natural",
    "natural-fuchsia": "Natural",
    "natural-lime": "Natural",
    "antique cherry red": "Red",
    "black-black": "Black",
    "sky blue-french navy": "French Navy",
    "orange": "Orange/Graphite Grey",
    "emerald-graphite": "Graphite",
}

DEFAULT_CUSTOM_LABEL = data_path("Custom Label Database.csv")
DEFAULT_PRODUCT_EXPORT = data_path("ProductExport.csv")


def norm(value: str) -> str:
    return (value or "").strip().casefold()


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
    raise RuntimeError(f"Could not decode file: {path}")


def cl_size_to_pe(size: str, spc: str = "") -> tuple[str, bool]:
    """Map Custom Label size to ProductExport size. Returns (pe_size, used_kids_map)."""
    key = norm(size)
    ns = norm(spc)

    adult = SIZE_TO_PRODUCT_EXPORT.get(key)
    if adult:
        return adult, False

    if ns in BZ_MONTH_SPCS:
        bz_mapped = BZ_AGE_TO_MONTH_CODE.get(key)
        if bz_mapped:
            return bz_mapped, True

    if ns in YOUTH_LETTER_SPCS:
        youth_mapped = YOUTH_AGE_TO_LETTER_SIZE.get(key)
        if youth_mapped:
            return youth_mapped, True

    return (size or "").strip(), False


def colours_to_try(colour_name: str) -> list[str]:
    """Normalized colour keys to try: original first, then alias."""
    raw = (colour_name or "").strip()
    if not raw:
        return []

    keys = [norm(raw)]
    alias = COLOUR_ALIASES.get(norm(raw))
    if alias:
        alias_key = norm(alias)
        if alias_key not in keys:
            keys.append(alias_key)
    return keys


def lookup_uid(
    lookup: dict[tuple[str, str, str], str],
    spc: str,
    colour_name: str,
    pe_size: str,
) -> tuple[str | None, bool]:
    """Return (uid, used_alias)."""
    ns = norm(spc)
    for i, colour_key in enumerate(colours_to_try(colour_name)):
        uid = lookup.get((ns, colour_key, pe_size))
        if uid:
            return uid, i > 0
    return None, False


def build_lookup(product_rows: list[dict[str, str]]) -> dict[tuple[str, str, str], str]:
    lookup: dict[tuple[str, str, str], str] = {}
    duplicates: list[tuple[tuple[str, str, str], str, str]] = []

    for row in product_rows:
        spc = (row.get("SPC") or "").strip()
        colour = norm(row.get("Colour Name") or "")
        size = (row.get("Size") or "").strip()
        uid = (row.get("UID") or "").strip()
        if not spc or not uid:
            continue

        key = (norm(spc), colour, size)
        if key in lookup and lookup[key] != uid:
            duplicates.append((key, lookup[key], uid))
        lookup[key] = uid

    return lookup, duplicates


def fill_stock_ids(
    custom_rows: list[dict[str, str]],
    lookup: dict[tuple[str, str, str], str],
) -> tuple[int, int, int, int, int, Counter[str]]:
    filled = 0
    filled_via_alias = 0
    filled_via_kids_size = 0
    unchanged_no_match = 0
    unchanged_no_spc = 0
    skip_reasons: Counter[str] = Counter()

    for row in custom_rows:
        spc = (row.get("BTC Product Code") or "").strip()
        if not spc:
            unchanged_no_spc += 1
            skip_reasons["empty_btc_product_code"] += 1
            continue

        pe_size, used_kids_size = cl_size_to_pe(row.get("Size") or "", spc)
        uid, used_alias = lookup_uid(lookup, spc, row.get("Colour Name") or "", pe_size)

        if not uid:
            unchanged_no_match += 1
            skip_reasons["no_match_in_product_export"] += 1
            continue

        row["BTC Stock ID"] = uid
        filled += 1
        if used_alias:
            filled_via_alias += 1
        if used_kids_size:
            filled_via_kids_size += 1

    return (
        filled,
        filled_via_alias,
        filled_via_kids_size,
        unchanged_no_match,
        unchanged_no_spc,
        skip_reasons,
    )


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    encoding: str,
) -> None:
    with open(path, "w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fill BTC Stock ID from ProductExport.csv using SPC + colour + size."
    )
    parser.add_argument(
        "--custom-label",
        type=Path,
        default=DEFAULT_CUSTOM_LABEL,
        help="Path to Custom Label Database.csv",
    )
    parser.add_argument(
        "--product-export",
        type=Path,
        default=DEFAULT_PRODUCT_EXPORT,
        help="Path to ProductExport.csv",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a .bak copy before overwriting the custom label file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report matches without writing changes",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write result here instead of overwriting --custom-label",
    )
    args = parser.parse_args()

    custom_path: Path = args.custom_label
    product_path: Path = args.product_export

    if not custom_path.is_file():
        print(f"Error: file not found: {custom_path}")
        return 1
    if not product_path.is_file():
        print(f"Error: file not found: {product_path}")
        return 1

    cl_fields, cl_rows, cl_encoding = load_csv(custom_path)
    _, pe_rows, pe_encoding = load_csv(product_path)

    if "BTC Stock ID" not in cl_fields:
        print("Error: Custom Label Database.csv has no 'BTC Stock ID' column")
        return 1

    lookup, duplicates = build_lookup(pe_rows)
    (
        filled,
        filled_via_alias,
        filled_via_kids_size,
        no_match,
        no_spc,
        skip_reasons,
    ) = fill_stock_ids(cl_rows, lookup)

    print(f"Custom label file: {custom_path}")
    print(f"Product export file: {product_path}")
    print(f"Encodings: custom={cl_encoding}, product={pe_encoding}")
    print(f"Custom label rows: {len(cl_rows)}")
    print(f"Product export lookup keys: {len(lookup)}")
    if duplicates:
        print(f"Warning: {len(duplicates)} duplicate ProductExport keys (last row wins)")
    print()
    print(f"BTC Stock ID updated: {filled}")
    print(f"  via colour alias: {filled_via_alias}")
    print(f"  via kids/age size map: {filled_via_kids_size}")
    print(f"No match (strict BTC Product Code): {no_match}")
    print(f"Skipped (empty BTC Product Code): {no_spc}")
    print()
    for reason, count in skip_reasons.most_common():
        print(f"  {reason}: {count}")

    if args.dry_run:
        print("\nDry run — no files changed.")
        return 0

    out_path = args.output or custom_path

    if not args.no_backup and out_path == custom_path:
        backup_path = custom_path.with_suffix(custom_path.suffix + ".bak")
        shutil.copy2(custom_path, backup_path)
        print(f"\nBackup written: {backup_path}")

    try:
        write_csv(out_path, cl_fields, cl_rows, cl_encoding)
    except PermissionError:
        fallback = custom_path.with_name(
            custom_path.stem + "_filled" + custom_path.suffix
        )
        write_csv(fallback, cl_fields, cl_rows, cl_encoding)
        print(
            f"\nCould not write {out_path} (file may be open in Excel/editor)."
        )
        print(f"Wrote instead: {fallback}")
        print("Close the original file and re-run, or replace it with the _filled copy.")
        return 0

    print(f"Updated: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
