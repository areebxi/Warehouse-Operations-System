"""
Download product (and optional brand) images into assets/ from BTC Product Data URLs.

Database.xlsx stores basenames only (Product_Image_URL / Brand_Image_URL). This script
fetches the files referenced in BTC Product Data (UID = SKU).
"""
from __future__ import annotations
import argparse
import time
from pathlib import Path
import pandas as pd
import requests
import app_paths  # noqa: F401
from app_paths import asset_path, data_path, product_database_path
PE_USECOLS = [
    "UID",
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
def pick_product_url(row: pd.Series) -> str:
    for col in ("image_url_high_res", "image_url_medium_res"):
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        s = str(val).strip()
        if s and not s.startswith("["):
            return s
    return ""
def load_btc_product_data(path: Path) -> pd.DataFrame:
    last_err: Exception | None = None
    df = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(
                path,
                usecols=PE_USECOLS,
                dtype={"UID": str},
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
    df = df[df["UID"] != ""]
    df = df.drop_duplicates(subset=["UID"], keep="first")
    return df
def database_filenames(path: Path) -> tuple[set[str], set[str]]:
    df = pd.read_excel(path, dtype={"SKU": str})
    product: set[str] = set()
    brand: set[str] = set()
    if "Product_Image_URL" in df.columns:
        product = {
            str(x).strip()
            for x in df["Product_Image_URL"].dropna()
            if str(x).strip()
        }
    if "Brand_Image_URL" in df.columns:
        brand = {
            str(x).strip()
            for x in df["Brand_Image_URL"].dropna()
            if str(x).strip()
        }
    return product, brand
def iter_download_jobs(
    pe_df: pd.DataFrame,
    *,
    skus: set[str] | None,
    database_only: bool,
    db_product_names: set[str],
    db_brand_names: set[str],
    include_products: bool,
    include_brands: bool,
):
    for _, row in pe_df.iterrows():
        uid = str(row["UID"]).strip()
        if skus and uid not in skus:
            continue

        if include_products:
            url = pick_product_url(row)
            name = filename_from_url(url)
            if name and (not database_only or name in db_product_names):
                yield "product", name, url, uid

        if include_brands:
            burl = row.get("brand image")
            bname = filename_from_url(burl)
            if bname and (not database_only or bname in db_brand_names):
                yield "brand", bname, str(burl).strip() if burl is not None else "", uid
def download_one(
    session: requests.Session,
    url: str,
    dest: Path,
    *,
    timeout: float,
) -> tuple[str, str]:
    """Returns (status, detail) where status is ok|skip|fail."""
    if dest.is_file() and dest.stat().st_size > 0:
        return "skip", "exists"
    if not url or url.startswith("["):
        return "fail", "no url"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        resp = session.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
        tmp.replace(dest)
        return "ok", str(dest)
    except requests.RequestException as e:
        return "fail", str(e)
