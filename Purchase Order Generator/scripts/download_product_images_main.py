"""CLI body for download_product_images."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import requests

from app_paths import product_database_path
from download_product_images_jobs import (
    database_filenames,
    download_one,
    iter_download_jobs,
    load_btc_product_data,
)


def run_main(*, default_btc: Path, product_dir: Path, brand_dir: Path) -> int:
    parser = argparse.ArgumentParser(
        description="Download product/brand images from BTC Product Data into assets."
    )
    parser.add_argument("--btc-product-data", type=Path, default=default_btc)
    parser.add_argument("--database", type=Path, default=product_database_path())
    parser.add_argument("--database-only", action="store_true")
    parser.add_argument("--sku", action="append", default=[], metavar="UID")
    parser.add_argument("--no-brands", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--delay", type=float, default=0.05)
    args = parser.parse_args()

    pe_path = args.btc_product_data
    if not pe_path.is_file():
        print(f"Error: file not found: {pe_path}")
        return 1

    pe_df = load_btc_product_data(pe_path)
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

    jobs = list(
        iter_download_jobs(
            pe_df,
            skus=skus,
            database_only=args.database_only,
            db_product_names=db_product_names,
            db_brand_names=db_brand_names,
            include_products=True,
            include_brands=not args.no_brands,
        )
    )

    ok = skip = fail = 0
    attempted = 0
    session = requests.Session()
    session.headers.setdefault("User-Agent", "PurchaseOrderApp/1.0")

    for kind, name, url, uid in jobs:
        if args.limit and attempted >= args.limit:
            break
        dest = product_dir / name if kind == "product" else brand_dir / name
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
        f"(jobs listed={len(jobs)}, product_dir={product_dir})"
    )
    if args.dry_run:
        print("Dry run — no files written.")
    return 0 if fail == 0 else 1
