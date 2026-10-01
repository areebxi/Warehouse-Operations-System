"""CLI for ShipStation Tags.xlsx sync."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .client import ShipStationError
from .sync_tags_xlsx import DEFAULT_XLSX_PATH, SyncResult, sync_shipstation_tags_xlsx


def _print_report(result: SyncResult) -> None:
    path = result.path or DEFAULT_XLSX_PATH
    mode = "DRY RUN - no changes written" if result.dry_run else "Synced"
    print(f"{mode}: {path}")
    print(f"  ShipStation tags : {result.live_count}")
    print(f"  Excel before     : {result.excel_count_before}")
    print(f"  Excel after      : {result.excel_count_after}")
    print(f"  Tag IDs updated  : {len(result.updated_ids)}")
    print(f"  Tags added       : {len(result.added)}")
    print(f"  Obsolete in Excel: {len(result.obsolete)} (kept; not deleted)")
    if result.backup_path:
        print(f"  Backup           : {result.backup_path}")
    if result.updated_ids:
        print("\nUpdated Tag IDs:")
        for name, old_id, new_id in result.updated_ids:
            print(f"  - {name}: {old_id} -> {new_id}")
    if result.added:
        print("\nAdded tags:")
        for name, tag_id in result.added:
            print(f"  - {name} ({tag_id})")
    if result.obsolete:
        print("\nObsolete in Excel (still in file):")
        for name, tag_id in result.obsolete:
            print(f"  - {name} ({tag_id})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Sync Data/ShipStation Tags.xlsx with current ShipStation tags "
            "(add missing names/IDs, update changed IDs)."
        )
    )
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=DEFAULT_XLSX_PATH,
        help=f"Path to ShipStation Tags workbook (default: {DEFAULT_XLSX_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing the file.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not write a .xlsx.bak before saving.",
    )
    args = parser.parse_args(argv)

    try:
        result = sync_shipstation_tags_xlsx(
            args.xlsx,
            dry_run=args.dry_run,
            backup=not args.no_backup,
        )
    except (ShipStationError, FileNotFoundError, ValueError, PermissionError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    _print_report(result)
    return 0
