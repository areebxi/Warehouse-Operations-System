#!/usr/bin/env python3
"""
Append missing SKUs to Database.xlsx from ProductExport.csv.

Database.xlsx.SKU == ProductExport.UID (BTC stock id).
Existing rows are never modified. New rows get Package left blank.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

import app_paths  # noqa: F401

from app_paths import DATA_DIR, PRODUCT_DATABASE_FILENAME, data_path, product_database_path

DEFAULT_DATABASE = product_database_path()
DEFAULT_PRODUCT_EXPORT = data_path("ProductExport.csv")

CORE_COLUMNS = [
    "SKU",
    "Product Code",
    "Brand",
    "Colour",
    "Size",
    "Description",
    "Product_Image_URL",
    "Brand_Image_URL",
    "Package",
]

PE_USECOLS = [
    "UID",
    "SPC",
    "Brand",
    "Colour Name",
    "Size",
    "Description",
    "image_url_high_res",
    "image_url_medium_res",
    "brand image",
]


def filename_from_url(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    s = str(value).strip()
    if not s or s.startswith("["):
        return ""
    return Path(s.replace("\\", "/")).name


def load_product_export(path: Path) -> pd.DataFrame:
    last_err: Exception | None = None
    df = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(
                path,
                usecols=PE_USECOLS,
                dtype={"UID": str, "SPC": str},
                encoding=encoding,
                low_memory=False,
            )
            break
        except UnicodeDecodeError as exc:
            last_err = exc
            continue
    if df is None:
        raise last_err or RuntimeError(f"Could not decode ProductExport: {path}")
    df["UID"] = df["UID"].astype(str).str.strip()
    df = df[~df["UID"].str.startswith("[", na=False)]
    df = df[df["UID"].astype(str) != ""]
    df = df.drop_duplicates(subset=["UID"], keep="first")
    return df


def load_database(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={"SKU": str})
    if "SKU" not in df.columns:
        raise ValueError(f"{path} has no SKU column")
    df["SKU"] = df["SKU"].astype(str).str.strip()
    return df


def export_row_to_database_row(pe_row: pd.Series) -> dict[str, str]:
    hi = pe_row.get("image_url_high_res")
    med = pe_row.get("image_url_medium_res")
    product_image = filename_from_url(hi if pd.notna(hi) and str(hi).strip() else med)
    return {
        "SKU": str(pe_row["UID"]).strip(),
        "Product Code": str(pe_row.get("SPC", "") or "").strip(),
        "Brand": str(pe_row.get("Brand", "") or "").strip(),
        "Colour": str(pe_row.get("Colour Name", "") or "").strip(),
        "Size": str(pe_row.get("Size", "") or "").strip(),
        "Description": str(pe_row.get("Description", "") or "").strip(),
        "Product_Image_URL": product_image,
        "Brand_Image_URL": filename_from_url(pe_row.get("brand image")),
        "Package": "",
    }


def build_missing_rows(db_df: pd.DataFrame, pe_df: pd.DataFrame) -> pd.DataFrame:
    existing = set(db_df["SKU"].dropna().astype(str).str.strip())
    missing_pe = pe_df[~pe_df["UID"].isin(existing)]
    if missing_pe.empty:
        return pd.DataFrame()

    new_rows = [export_row_to_database_row(row) for _, row in missing_pe.iterrows()]
    new_df = pd.DataFrame(new_rows)

    for col in db_df.columns:
        if col not in new_df.columns:
            new_df[col] = pd.NA
    for col in CORE_COLUMNS:
        if col not in db_df.columns:
            db_df[col] = pd.NA

    extra_cols = [c for c in db_df.columns if c not in new_df.columns]
    for col in extra_cols:
        new_df[col] = pd.NA

    return new_df[db_df.columns]


def backup_database(path: Path) -> Path:
    archive_dir = DATA_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = archive_dir / f"{PRODUCT_DATABASE_FILENAME}.bak_{stamp}"
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append missing SKUs to Database.xlsx from ProductExport.csv (SKU = UID)."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Path to Database.xlsx",
    )
    parser.add_argument(
        "--product-export",
        type=Path,
        default=DEFAULT_PRODUCT_EXPORT,
        help="Path to ProductExport.csv",
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
    pe_path: Path = args.product_export

    if not db_path.is_file():
        print(f"Error: file not found: {db_path}")
        return 1
    if not pe_path.is_file():
        print(f"Error: file not found: {pe_path}")
        return 1

    db_df = load_database(db_path)
    pe_df = load_product_export(pe_path)
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
