#!/usr/bin/env python3
"""
Download product (and optional brand) images into assets/ from ProductExport.csv URLs.

Database.xlsx stores basenames only (Product_Image_URL / Brand_Image_URL). This script
fetches the files referenced in ProductExport (UID = SKU).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

import app_paths  # noqa: F401

from app_paths import asset_path, data_path, product_database_path

DEFAULT_PRODUCT_EXPORT = data_path("ProductExport.csv")
PRODUCT_IMAGE_DIR = asset_path("product_images")
BRAND_IMAGE_DIR = asset_path("brand_logos")

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


def load_product_export(path: Path) -> pd.DataFrame:
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
        raise last_err or RuntimeError(f"Could not decode ProductExport: {path}")
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download product/brand images from ProductExport.csv into assets/."
    )
    parser.add_argument("--product-export", type=Path, default=DEFAULT_PRODUCT_EXPORT)
    parser.add_argument("--database", type=Path, default=product_database_path())
    parser.add_argument(
        "--database-only",
        action="store_true",
        help="Only download filenames referenced in Database.xlsx (recommended for PDFs).",
    )
    parser.add_argument(
        "--sku",
        action="append",
        default=[],
        metavar="UID",
        help="Limit to one or more BTC stock ids (UID). Can be repeated.",
    )
    parser.add_argument("--no-brands", action="store_true", help="Skip brand logos.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Max downloads to attempt (0 = no limit).")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--delay", type=float, default=0.05, help="Seconds between HTTP requests.")
    args = parser.parse_args()

    pe_path = args.product_export
    if not pe_path.is_file():
        print(f"Error: file not found: {pe_path}")
        return 1

    pe_df = load_product_export(pe_path)
    skus = {s.strip() for s in args.sku if s.strip()} or None

    db_product_names: set[str] = set()
    db_brand_names: set[str] = set()
    if args.database_only:
        if not args.database.is_file():
            print(f"Error: database not found: {args.database}")
            return 1
        db_product_names, db_brand_names = database_filenames(args.database)
        print(f"Database product image names: {len(db_product_names)}")
        print(f"Database brand image names: {len(db_brand_names)}")

    include_products = True
    include_brands = not args.no_brands

    jobs = list(
        iter_download_jobs(
            pe_df,
            skus=skus,
            database_only=args.database_only,
            db_product_names=db_product_names,
            db_brand_names=db_brand_names,
            include_products=include_products,
            include_brands=include_brands,
        )
    )

    ok = skip = fail = 0
    attempted = 0
    session = requests.Session()
    session.headers.setdefault("User-Agent", "PurchaseOrderApp/1.0")

    for kind, name, url, uid in jobs:
        if args.limit and attempted >= args.limit:
            break
        dest = PRODUCT_IMAGE_DIR / name if kind == "product" else BRAND_IMAGE_DIR / name
        if dest.is_file() and dest.stat().st_size > 0:
            skip += 1
            continue
        if args.dry_run:
            print(f"would download [{kind}] uid={uid} -> {dest.name}")
            attempted += 1
            continue
        status, detail = download_one(session, url, dest, timeout=args.timeout)
        attempted += 1
        if status == "ok":
            ok += 1
            if ok <= 10 or (skus and uid in skus):
                print(f"OK [{kind}] uid={uid} -> {dest.name}")
        elif status == "skip":
            skip += 1
        else:
            fail += 1
            print(f"FAIL [{kind}] uid={uid} {name}: {detail}")
        if args.delay > 0:
            time.sleep(args.delay)

    print(
        f"\nDone. downloaded={ok} skipped={skip} failed={fail} "
        f"(jobs listed={len(jobs)}, product_dir={PRODUCT_IMAGE_DIR})"
    )
    if args.dry_run:
        print("Dry run — no files written.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
