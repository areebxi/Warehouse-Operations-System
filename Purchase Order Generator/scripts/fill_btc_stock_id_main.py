"""CLI main for fill_btc_stock_id."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from fill_btc_stock_id_lookup import build_lookup, fill_stock_ids, load_csv, write_csv


def main(
    *,
    default_custom_label: Path,
    default_btc_product_data: Path,
) -> int:
    parser = argparse.ArgumentParser(
        description="Fill BTC Stock ID from BTC Product Data using SPC + colour + size."
    )
    parser.add_argument("--custom-label", type=Path, default=default_custom_label)
    parser.add_argument("--btc-product-data", type=Path, default=default_btc_product_data)
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    custom_path: Path = args.custom_label
    product_path: Path = args.btc_product_data
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
        print(f"Warning: {len(duplicates)} duplicate BTC Product Data keys (last row wins)")
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
        fallback = custom_path.with_name(custom_path.stem + "_filled" + custom_path.suffix)
        write_csv(fallback, cl_fields, cl_rows, cl_encoding)
        print(f"\nCould not write {out_path} (file may be open in Excel/editor).")
        print(f"Wrote instead: {fallback}")
        print("Close the original file and re-run, or replace it with the _filled copy.")
        return 0

    print(f"Updated: {out_path}")
    return 0
