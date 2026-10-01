"""
Append missing SKUs to Database.xlsx from BTC Product Data.

Database.xlsx.SKU == BTC Product Data UID (BTC stock id).
Existing rows are never modified. New rows get Package left blank.
"""
from __future__ import annotations
import argparse
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
import app_paths  # noqa: F401
from app_paths import (
    PRODUCT_DATABASE_FILENAME,
    data_path,
    product_database_archive_dir,
    product_database_path,
)
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
def load_btc_product_data(path: Path) -> pd.DataFrame:
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
        raise last_err or RuntimeError(f"Could not decode BTC Product Data: {path}")
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
    archive_dir = product_database_archive_dir()
    archive_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = archive_dir / f"{PRODUCT_DATABASE_FILENAME}.bak_{stamp}"
    shutil.copy2(path, backup_path)
    return backup_path
