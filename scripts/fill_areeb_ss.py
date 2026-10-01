"""ShipStation order-SKU fetch + CL leftover analysis for fill_areeb_taxonomy."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from fill_areeb_util import SS_STATUSES
from shared import paths as wh
from shared.areeb_taxonomy import cell, classify_cl
from shared.cl_sku_match import build_label_index, match_keys, normalize_label


def ss_cache_path() -> Path:
    return wh.cl_app_dir() / "docs" / "areeb-taxonomy-ss-skus.json"


def extract_skus(orders: list[dict]) -> list[str]:
    skus: list[str] = []
    for order in orders:
        items = order.get("items") or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            sku = cell(item.get("sku") or item.get("SKU"))
            if sku:
                skus.append(sku)
    return skus


def ss_page_cache_path() -> Path:
    return wh.cl_app_dir() / "docs" / "areeb-taxonomy-ss-pages.jsonl"


def iter_page_cache(path: Path):
    """Yield parsed jsonl page records; skip blank/truncated lines."""
    if not path.is_file():
        return
    with path.open(encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            yield rec


def read_page_cache(path: Path) -> dict[str, set[int]]:
    done: dict[str, set[int]] = defaultdict(set)
    for rec in iter_page_cache(path):
        done[str(rec.get("status") or "")].add(int(rec.get("page") or 0))
    return done


def fetch_year_skus(*, cache: Path, refresh: bool) -> list[str]:
    if cache.is_file() and not refresh:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("complete"):
            skus = [cell(s) for s in data.get("skus") or [] if cell(s)]
            print(f"ShipStation SKU cache {cache} ({len(skus):,} SKUs)")
            return skus
    from shared.shipstation import ShipStationClient

    end = date.today()
    start = end - timedelta(days=365)
    start_s = start.isoformat()
    end_s = end.isoformat()
    page_cache = ss_page_cache_path()
    if refresh and page_cache.is_file():
        page_cache.unlink()
    done_pages = read_page_cache(page_cache)
    print(f"Fetching ShipStation orders {start_s} .. {end_s} statuses={SS_STATUSES}")
    client = ShipStationClient(log=lambda m: print(" ", m, flush=True))
    all_skus: list[str] = []
    for rec in iter_page_cache(page_cache):
        all_skus.extend(rec.get("skus") or [])
    if all_skus:
        print(f"  resumed {len(all_skus):,} SKUs from {page_cache.name}")

    page_cache.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for status in SS_STATUSES:
        have = done_pages.get(status) or set()
        start_page = (max(have) + 1) if have else 1

        def on_page(page: int, total: int, batch: list, *, _status=status) -> None:
            skus = extract_skus(batch)
            all_skus.extend(skus)
            with page_cache.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps({"status": _status, "page": page, "pages": total, "skus": skus})
                    + "\n"
                )
            counts[_status] = counts.get(_status, 0) + len(batch)

        if have:
            print(f"  {status}: resume at page {start_page} (have {len(have)} pages)")
        client.list_orders(
            order_status=status,
            order_date_start=start_s,
            order_date_end=end_s,
            page_pause_s=2.5,
            start_page=start_page,
            collect=False,
            on_page=on_page,
        )
        print(f"  {status}: orders~{counts.get(status, 0):,}")
    unique = sorted(set(cell(s) for s in all_skus if cell(s)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "complete": True,
                "start": start_s,
                "end": end_s,
                "statuses": list(SS_STATUSES),
                "orders_by_status": counts,
                "sku_count": len(unique),
                "skus": unique,
            },
            indent=0,
        ),
        encoding="utf-8",
    )
    print(f"  cached {len(unique):,} unique SKUs -> {cache}")
    return unique


def analyze_orders_vs_cl(skus: list[str], cl_rows: list[dict[str, str]]) -> None:
    labels = [r.get("Custom Label") or "" for r in cl_rows]
    index = build_label_index(labels, ids=range(len(cl_rows)))
    source_c = Counter()
    leftover_ga = Counter()
    leftover_cat = Counter()
    unmatched_sku = Counter()
    matched = 0
    for sku in skus:
        hit_id = None
        for key in match_keys(sku):
            hit_id = index.get(normalize_label(key))
            if hit_id is not None:
                break
        if hit_id is None:
            unmatched_sku[sku] += 1
            continue
        matched += 1
        row = cl_rows[int(hit_id)]
        values = classify_cl(row)
        source_c[values.source or "none"] += 1
        if not values.category:
            leftover_ga[cell(row.get("Gender Apparel")) or "(blank GA)"] += 1
            leftover_cat[cell(row.get("Category")) or "(blank Category)"] += 1
    print("\n=== Order SKUs vs CL (last year cache) ===")
    print(f"  unique order SKUs: {len(skus):,}")
    print(f"  matched a CL row: {matched:,}")
    print(f"  no CL row: {sum(unmatched_sku.values()):,} distinct={len(unmatched_sku):,}")
    print("  classify source on matched:")
    for k, n in source_c.most_common():
        print(f"    {k or 'none'}: {n:,}")
    print("  leftover still-blank Category (Areeb) Gender Apparel (top 15):")
    for k, n in leftover_ga.most_common(15):
        print(f"    {n:6,}  {k}")
    print("  leftover Category (top 10):")
    for k, n in leftover_cat.most_common(10):
        print(f"    {n:6,}  {k}")
    print("  unmatched order SKUs (top 15):")
    for k, n in unmatched_sku.most_common(15):
        print(f"    {n:6,}  {k}")
