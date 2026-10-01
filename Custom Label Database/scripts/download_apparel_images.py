"""
Download apparel images for Custom Label Database mock rows.

Uses BTC Product Data `colour image 01` as the URL.
Saves each file as the exact `Apparel Image` name (+ extension from URL).

Default scope: mock rows (Custom Label ^M\\d+) that were added by
generate_from_mocks (not present in the preGenerate backup). Use --all-mocks
for every M## row.

Example (from Custom Label Database app root):

  python scripts/download_apparel_images.py
  python scripts/download_apparel_images.py --all-mocks
  python scripts/download_apparel_images.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO = SCRIPTS_DIR.parent
_WAREHOUSE = REPO.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
from scripts.download_apparel_images_impl import download_one, load_pe, build_download_plan, load_existing_labels, url_extension, extract_uid, clean

DEFAULT_DB = wh.cl_csv_path(REPO)
DEFAULT_PE = wh.btc_product_data_path(REPO)
DEFAULT_OUT = wh.images_apparel_dir(REPO)
DEFAULT_PRE_GENERATE = (
    wh.cl_backups_dir(REPO) / "Custom Label Database_preGenerate_20260820_171255.xlsx"
)

RE_MOCK = re.compile(r"(?i)^M\d+")
RE_UID = re.compile(r"-(\d+)$")
COLOUR_IMAGE_COL = "colour image 01"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Download mock Apparel Images from BTC Product Data colour image 01."
    )
    ap.add_argument("--db", type=Path, default=DEFAULT_DB, help="Custom_Label_Database.csv")
    ap.add_argument(
        "--product",
        type=Path,
        default=None,
        help="BTC Product Data .xlsx or .csv (default: database/shared/btc_product_data/BTC_Product_Data.csv)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Output folder (default: Apparel Images/)",
    )
    ap.add_argument(
        "--all-mocks",
        action="store_true",
        help="Download for all M## rows (not only generate_from_mocks additions)",
    )
    ap.add_argument(
        "--pre-generate",
        type=Path,
        default=DEFAULT_PRE_GENERATE,
        help="Backup used to detect newly added mocks",
    )
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Max unique images (0=all)")
    args = ap.parse_args()

    pe_path = args.product
    if pe_path is None:
        pe_path = DEFAULT_PE
    if not args.db.exists():
        raise SystemExit(f"DB not found: {args.db}")
    if not pe_path.exists():
        raise SystemExit(f"BTC Product Data not found: {pe_path}")

    print(f"DB: {args.db}", flush=True)
    print(f"PE: {pe_path}", flush=True)
    print(f"Out: {args.out}", flush=True)

    db = pd.read_csv(
        args.db,
        dtype=str,
        low_memory=False,
        usecols=lambda c: c
        in ("Custom Label", "Apparel Image", "Supplier SKU", "Gender Apparel", "Colour"),
    )
    for c in db.columns:
        db[c] = clean(db[c])

    is_mock = db["Custom Label"].str.match(RE_MOCK, na=False)
    if args.all_mocks:
        scope = db.loc[is_mock].copy()
        print(f"Scope: all M## rows ({len(scope):,})", flush=True)
    else:
        old = load_existing_labels(args.pre_generate)
        if not old:
            print(
                "WARNING: pre-generate backup missing — falling back to all M## rows.",
                flush=True,
            )
            scope = db.loc[is_mock].copy()
        else:
            scope = db.loc[is_mock & ~db["Custom Label"].isin(old)].copy()
            print(
                f"Scope: newly added M## vs preGenerate ({len(scope):,} rows)",
                flush=True,
            )

    pe = load_pe(pe_path)
    plan = build_download_plan(scope, pe)
    if args.limit > 0:
        plan = plan.head(args.limit)

    no_url = (
        scope["Apparel Image"].ne("")
        & scope["Custom Label"].map(extract_uid).map(pe[COLOUR_IMAGE_COL]).fillna("").eq("")
    )
    print(f"Unique Apparel Image files to fetch: {len(plan):,}", flush=True)
    print(f"Scope rows missing PE colour image 01: {int(no_url.sum()):,}", flush=True)

    if args.dry_run:
        print("\nDry-run samples:", flush=True)
        for _, r in plan.head(8).iterrows():
            print(f"  {r['Apparel Image']}  <-  {r['url'][:70]}", flush=True)
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    ok = skip = fail = 0
    t0 = time.time()

    def job(row: pd.Series) -> tuple[str, str]:
        name = row["Apparel Image"]
        url = row["url"]
        ext = url_extension(url)
        # Exact Apparel Image name; do not re-sanitize
        out_path = args.out / f"{name}{ext}"
        return download_one(url, out_path)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {ex.submit(job, row): row["Apparel Image"] for _, row in plan.iterrows()}
        done = 0
        total = len(futures)
        for fut in as_completed(futures):
            done += 1
            status, detail = fut.result()
            if status == "ok":
                ok += 1
            elif status == "skip":
                skip += 1
            else:
                fail += 1
                failures.append(detail)
            if done % 25 == 0 or done == total:
                print(
                    f"  [{done}/{total}] ok={ok} skip={skip} fail={fail}",
                    flush=True,
                )

    elapsed = time.time() - t0
    print(
        f"\nDone in {elapsed:.1f}s — downloaded={ok} skipped={skip} failed={fail}",
        flush=True,
    )
    print(f"Images folder: {args.out}", flush=True)
    if failures:
        fail_path = args.out / "download-failures-colour-image-01.txt"
        fail_path.write_text("\n".join(failures) + "\n", encoding="utf-8")
        print(f"Failures logged: {fail_path}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        raise SystemExit(130)
