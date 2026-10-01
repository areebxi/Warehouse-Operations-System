from __future__ import annotations
import app_paths  # noqa: F401
from sync_database_btc_helpers import (
filename_from_url, load_btc_product_data, load_database, export_row_to_database_row, build_missing_rows, backup_database
)
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append missing SKUs to Database.xlsx from BTC Product Data (SKU = UID)."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Path to Database.xlsx",
    )
    parser.add_argument(
        "--btc-product-data",
        type=Path,
        default=DEFAULT_BTC_PRODUCT_DATA,
        help="Path to BTC_Product_Data.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write result here instead of overwriting --database",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup before overwriting --database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many rows would be added without writing",
    )
    args = parser.parse_args()

    db_path: Path = args.database
    pe_path: Path = args.btc_product_data

    if not db_path.is_file():
        print(f"Error: file not found: {db_path}")
        return 1
    if not pe_path.is_file():
        print(f"Error: file not found: {pe_path}")
        return 1

    db_df = load_database(db_path)
    pe_df = load_btc_product_data(pe_path)
    new_df = build_missing_rows(db_df, pe_df)

    existing_count = len(db_df)
    add_count = len(new_df)
    print(f"Database: {db_path}")
    print(f"Product export: {pe_path}")
    print(f"Existing database rows: {existing_count}")
    print(f"Product export rows (deduped): {len(pe_df)}")
    print(f"Rows to append: {add_count}")

    if add_count and add_count <= 20:
        print("Sample new SKUs:", ", ".join(new_df["SKU"].astype(str).head(20).tolist()))
    elif add_count:
        sample = new_df["SKU"].astype(str).head(10).tolist()
        print("Sample new SKUs (first 10):", ", ".join(sample))

    if args.dry_run:
        print("\nDry run — no files changed.")
        return 0

    if add_count == 0:
        print("\nNothing to add.")
        return 0

    out_path = args.output or db_path
    combined = pd.concat([db_df, new_df], ignore_index=True)

    if not args.no_backup and out_path.resolve() == db_path.resolve():
        backup_path = backup_database(db_path)
        print(f"\nBackup written: {backup_path}")

    try:
        combined.to_excel(out_path, index=False, engine="openpyxl")
    except PermissionError:
        fallback = db_path.with_name(db_path.stem + "_synced" + db_path.suffix)
        combined.to_excel(fallback, index=False, engine="openpyxl")
        print(f"\nCould not write {out_path} (file may be open in Excel).")
        print(f"Wrote instead: {fallback}")
        return 0

    print(f"Updated: {out_path} ({existing_count} -> {len(combined)} rows)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

