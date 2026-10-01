"""Fill Category/Product Type/Product Style/Department (Areeb) on CL, Plain, Packs.

  python scripts/fill_areeb_taxonomy.py --target plain --dry-run
  python scripts/fill_areeb_taxonomy.py --target packs --dry-run
  python scripts/fill_areeb_taxonomy.py --target cl --dry-run --fetch-orders
  python scripts/fill_areeb_taxonomy.py --target all
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fill_areeb_cl import cl_rows, fill_cl
from fill_areeb_packs import fill_packs
from fill_areeb_plain import fill_plain
from fill_areeb_ss import analyze_orders_vs_cl, fetch_year_skus, ss_cache_path
from fill_areeb_util import PACKS_SHEET, PLAIN_SHEET, SS_STATUSES  # noqa: F401
from shared import paths as wh
from shared.areeb_taxonomy import AreebCatalogs, cell, load_catalogs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", choices=("plain", "packs", "cl", "all"), default="all")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--fetch-orders", action="store_true", help="Pull last 12 months of ShipStation SKUs")
    p.add_argument("--refresh-orders", action="store_true", help="Ignore SKU cache and fetch again")
    p.add_argument(
        "--orders-only",
        action="store_true",
        help="Skip catalog fills; fetch/analyze last-year SKUs only",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    dry = args.dry_run
    if dry:
        print("DRY RUN — no catalog writes\n", flush=True)
    targets = () if args.orders_only else (("plain", "packs", "cl") if args.target == "all" else (args.target,))
    cat: AreebCatalogs | None = None
    if "plain" in targets or "packs" in targets:
        print("Loading BTC + Uneek catalogs…", flush=True)
        cat = load_catalogs()
        print(
            f"  BTC UIDs={len(cat.btc_by_uid)//2:,} SPC={len(cat.btc_by_spc)//2:,} "
            f"Uneek short={len(cat.uneek_by_short)//2:,} code={len(cat.uneek_by_code)//2:,}",
            flush=True,
        )
    cl_rows_for_analysis: list[dict[str, str]] = []
    if "plain" in targets:
        assert cat is not None
        fill_plain(cat, dry_run=dry)
    if "packs" in targets:
        assert cat is not None
        fill_packs(cat, dry_run=dry)
    if "cl" in targets:
        _stats, leftover = fill_cl(dry_run=dry)
        _, cl_rows_for_analysis = cl_rows(wh.cl_csv_path())
        ga = Counter(cell(r.get("Gender Apparel")) or "(blank)" for r in leftover)
        print("CL still-blank Category (Areeb) Gender Apparel top 12:")
        for k, n in ga.most_common(12):
            print(f"    {n:6,}  {k}")
    if args.fetch_orders or args.refresh_orders or args.orders_only:
        skus = fetch_year_skus(cache=ss_cache_path(), refresh=args.refresh_orders)
        if not cl_rows_for_analysis:
            _, cl_rows_for_analysis = cl_rows(wh.cl_csv_path())
        analyze_orders_vs_cl(skus, cl_rows_for_analysis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
