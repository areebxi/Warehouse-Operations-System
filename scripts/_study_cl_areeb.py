"""One-shot study: CL Gender Apparel vs last-year ShipStation SKUs. No BTC/Uneek."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import paths as wh
from shared.areeb_taxonomy import CL_LEFTOVER_RULES, cell
from shared.cl_sku_match import build_label_index, match_keys, normalize_label


def load_ss_skus() -> list[str]:
    cache = wh.cl_app_dir() / "docs" / "areeb-taxonomy-ss-skus.json"
    data = json.loads(cache.read_text(encoding="utf-8"))
    return list(data.get("skus") or [])


def main() -> None:
    path = wh.cl_csv_path()
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            rows.append({k: cell(v) for k, v in row.items()})
    print(f"CL rows: {len(rows):,}")

    ga_c = Counter()
    cat_c = Counter()
    brand_c = Counter()
    blank_ga = 0
    for row in rows:
        ga = row.get("Gender Apparel") or "(blank)"
        ga_c[ga] += 1
        if ga == "(blank)":
            blank_ga += 1
        cat_c[row.get("Category") or "(blank)"] += 1
        brand_c[row.get("Brand") or "(blank)"] += 1

    known = set(CL_LEFTOVER_RULES) | {k.casefold() for k in CL_LEFTOVER_RULES}
    uncovered = [(n, g) for g, n in ga_c.items() if g != "(blank)" and g not in CL_LEFTOVER_RULES and g.casefold() not in known]
    uncovered.sort(reverse=True)

    print(f"unique Gender Apparel: {len(ga_c):,}  blank GA rows: {blank_ga:,}")
    print(f"GA values not in exact leftover table: {len(uncovered):,} values, {sum(n for n,_ in uncovered):,} rows")
    print("\nTop 40 Gender Apparel by CL rows:")
    for g, n in ga_c.most_common(40):
        flag = "TABLE" if g in CL_LEFTOVER_RULES or g.casefold() in known else "MISS"
        print(f"  {n:7,}  {flag:5}  {g}")

    print("\nUncovered GA (top 80 by rows):")
    for n, g in uncovered[:80]:
        print(f"  {n:7,}  {g}")

    print("\nCL Category (top 25):")
    for k, n in cat_c.most_common(25):
        print(f"  {n:7,}  {k}")

    # last-year orders
    skus = load_ss_skus()
    labels = [r.get("Custom Label") or "" for r in rows]
    index = build_label_index(labels, ids=range(len(rows)))
    order_ga = Counter()
    order_uncovered = Counter()
    matched = 0
    no_row = 0
    for sku in skus:
        hit_id = None
        for key in match_keys(sku):
            hit_id = index.get(normalize_label(key))
            if hit_id is not None:
                break
        if hit_id is None:
            no_row += 1
            continue
        matched += 1
        ga = rows[int(hit_id)].get("Gender Apparel") or "(blank)"
        order_ga[ga] += 1
        if ga != "(blank)" and ga not in CL_LEFTOVER_RULES and ga.casefold() not in known:
            order_uncovered[ga] += 1
    print(f"\nLast-year unique SKUs: {len(skus):,}  matched CL: {matched:,}  no CL: {no_row:,}")
    print("Top 40 Gender Apparel by last-year matched SKUs:")
    for g, n in order_ga.most_common(40):
        flag = "TABLE" if g in CL_LEFTOVER_RULES or g.casefold() in known else "MISS"
        print(f"  {n:7,}  {flag:5}  {g}")
    print("\nUncovered GA among last-year matched SKUs:")
    for g, n in order_uncovered.most_common(50):
        print(f"  {n:7,}  {g}")

    # blank GA: sample Custom Label / Category / Brand
    print("\nBlank Gender Apparel samples (up to 20):")
    shown = 0
    for row in rows:
        if row.get("Gender Apparel"):
            continue
        print(
            f"  label={row.get('Custom Label')!r} cat={row.get('Category')!r} "
            f"sub={row.get('Sub-Category')!r} brand={row.get('Brand')!r}"
        )
        shown += 1
        if shown >= 20:
            break


if __name__ == "__main__":
    main()
