#!/usr/bin/env python3
"""
Validate that every BTC Product Code in Custom Label Database.csv
exists as SPC in ProductExport.csv.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import app_paths  # noqa: F401

from app_paths import data_path

DEFAULT_CUSTOM_LABEL = data_path("Custom Label Database.csv")
DEFAULT_PRODUCT_EXPORT = data_path("ProductExport.csv")


def load_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with open(path, encoding=encoding, newline="") as handle:
                return list(csv.DictReader(handle))
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate BTC Product Code values against ProductExport SPC."
    )
    parser.add_argument("--custom-label", type=Path, default=DEFAULT_CUSTOM_LABEL)
    parser.add_argument("--product-export", type=Path, default=DEFAULT_PRODUCT_EXPORT)
    parser.add_argument(
        "--export-missing",
        type=Path,
        default=None,
        help="Optional path to write rows with invalid BTC Product Code",
    )
    args = parser.parse_args()

    cl_rows = load_csv(args.custom_label)
    pe_rows = load_csv(args.product_export)

    spc_values = {(r.get("SPC") or "").strip() for r in pe_rows if (r.get("SPC") or "").strip()}
    spc_lookup = {s.casefold(): s for s in spc_values}

    empty_rows = 0
    valid_rows = 0
    invalid_rows: list[dict[str, str]] = []
    code_use: Counter[str] = Counter()

    for row in cl_rows:
        code = (row.get("BTC Product Code") or "").strip()
        if not code:
            empty_rows += 1
            continue
        code_use[code] += 1
        if code.casefold() in spc_lookup:
            valid_rows += 1
        else:
            invalid_rows.append(row)

    unique_codes = set(code_use)
    missing_codes = sorted(c for c in unique_codes if c.casefold() not in spc_lookup)

    print(f"Custom label rows: {len(cl_rows)}")
    print(f"ProductExport unique SPC values: {len(spc_values)}")
    print()
    print(f"Rows with empty BTC Product Code: {empty_rows}")
    print(f"Rows with BTC Product Code: {len(cl_rows) - empty_rows}")
    print(f"Unique BTC Product Codes: {len(unique_codes)}")
    print(f"  Valid (in SPC): {len(unique_codes) - len(missing_codes)}")
    print(f"  Invalid (not in SPC): {len(missing_codes)}")
    print()
    print(f"Rows with valid code: {valid_rows}")
    print(f"Rows with invalid code: {len(invalid_rows)}")

    if missing_codes:
        print("\nInvalid BTC Product Codes:")
        for code in missing_codes:
            print(f"  {code!r}  ({code_use[code]} rows)")
        print("\nNote: empty BTC Product Code rows are not validated.")

    if args.export_missing and invalid_rows:
        fieldnames = list(invalid_rows[0].keys())
        with open(args.export_missing, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(invalid_rows)
        print(f"\nWrote invalid rows: {args.export_missing}")

    return 1 if missing_codes else 0


if __name__ == "__main__":
    raise SystemExit(main())
