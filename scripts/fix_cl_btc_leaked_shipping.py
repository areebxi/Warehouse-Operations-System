"""Clear Package Type / Weight / Service values that leaked into CL BTC columns.

  python scripts/fix_cl_btc_leaked_shipping.py --dry-run
  python scripts/fix_cl_btc_leaked_shipping.py
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import paths as wh

COL_SKU = "BTC SKU"
COL_PC = "BTC Product Code"
COL_STOCK = "BTC Supplier Stock"
COL_PKG = "Package Type"
COL_WEIGHT = "Weight"
COL_SERVICE = "Service"
COL_SUP_NAME = "Supplier Name"
COL_SUP_SKU = "Supplier SKU"
COL_SUP_PC = "Supplier Product Code"
COL_SUP_STOCK = "Supplier Stock"

PACKAGE_TYPES = frozenset(
    {
        "large letter",
        "parcel",
        "small parcel",
        "rm small parcel",
        "rm large letter",
        "letter",
        "large parcel",
        "packet",
        "prime parcel",
        "prime letter",
    }
)
SERVICE_EXACT = frozenset(
    {
        "royal mail48",
        "royal mail 48 - crl",
        "tracked 24 - tpn",
        "uk_royalmail48",
    }
)
SERVICE_HINTS = ("royal mail", "tracked 24", "tracked 48", "letterbox", "parcelforce")


def cell(val) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return s


def is_package_type(val: str) -> bool:
    return cell(val).casefold() in PACKAGE_TYPES


def is_shipping_service(val: str) -> bool:
    v = cell(val).casefold()
    if not v:
        return False
    if v in SERVICE_EXACT:
        return True
    return any(h in v for h in SERVICE_HINTS)


def is_btc_name(val: str) -> bool:
    return "btc" in cell(val).casefold()


def sku_is_leaked(sku: str) -> bool:
    return bool(cell(sku)) and is_package_type(sku)


def stock_is_leaked(stock: str) -> bool:
    return bool(cell(stock)) and is_shipping_service(stock)


def pc_is_leaked(pc: str, *, sku: str, stock: str, weight: str, supplier_pc: str) -> bool:
    """True when BTC Product Code is a Weight (g) copy, not an SPC."""
    pc = cell(pc)
    if not pc:
        return False
    if cell(weight) and pc == cell(weight):
        return True
    if (sku_is_leaked(sku) or stock_is_leaked(stock)) and pc != cell(supplier_pc):
        return True
    return False


def plan_row(row: dict) -> dict:
    """Return patched fields for one CL row. Unchanged keys are omitted."""
    sku = cell(row.get(COL_SKU))
    pc = cell(row.get(COL_PC))
    stock = cell(row.get(COL_STOCK))
    pkg = cell(row.get(COL_PKG))
    weight = cell(row.get(COL_WEIGHT))
    service = cell(row.get(COL_SERVICE))
    sup_sku = cell(row.get(COL_SUP_SKU))
    sup_pc = cell(row.get(COL_SUP_PC))
    sup_stock = cell(row.get(COL_SUP_STOCK))
    btc = is_btc_name(row.get(COL_SUP_NAME))

    out: dict[str, str] = {}
    if sku_is_leaked(sku):
        if not pkg:
            out[COL_PKG] = sku
        out[COL_SKU] = sup_sku if btc and sup_sku else ""
    if pc_is_leaked(pc, sku=sku, stock=stock, weight=weight, supplier_pc=sup_pc):
        if not weight and pc.isdigit():
            out[COL_WEIGHT] = pc
        out[COL_PC] = sup_pc if btc and sup_pc else ""
    if stock_is_leaked(stock):
        if not service:
            out[COL_SERVICE] = stock
        out[COL_STOCK] = sup_stock if btc and sup_stock else ""
    return {k: v for k, v in out.items() if cell(row.get(k)) != v}


def backup_file(path: Path) -> Path:
    dest_dir = wh.cl_backups_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{path.stem}.bak_{stamp}{path.suffix}"
    shutil.copy2(path, dest)
    return dest


def run(*, dry_run: bool) -> dict[str, int]:
    path = wh.cl_csv_path()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = list(reader)

    stats: dict[str, int] = defaultdict(int)
    stats["rows"] = len(rows)
    samples: list[str] = []

    for row in rows:
        patch = plan_row(row)
        if not patch:
            continue
        stats["rows_touched"] += 1
        for col, value in patch.items():
            key = f"wrote_{col}" if not dry_run else f"would_{col}"
            stats[key] += 1
            if value == "":
                stats[f"cleared_{col}"] += 1
            elif cell(row.get(col)) == "":
                stats[f"restored_or_refilled_{col}"] += 1
            else:
                stats[f"replaced_{col}"] += 1
            row[col] = value
        if len(samples) < 6:
            samples.append(
                f"{cell(row.get('Custom Label'))} "
                f"SKU={cell(row.get(COL_SKU))!r} PC={cell(row.get(COL_PC))!r} "
                f"Stock={cell(row.get(COL_STOCK))!r} pkg={cell(row.get(COL_PKG))!r} "
                f"wt={cell(row.get(COL_WEIGHT))!r} svc={cell(row.get(COL_SERVICE))!r}"
            )

    print(f"Custom Label: {path}")
    for key in (
        "rows",
        "rows_touched",
        "cleared_BTC SKU",
        "cleared_BTC Product Code",
        "cleared_BTC Supplier Stock",
        "replaced_BTC SKU",
        "replaced_BTC Product Code",
        "replaced_BTC Supplier Stock",
        "restored_or_refilled_Package Type",
        "restored_or_refilled_Weight",
        "restored_or_refilled_Service",
        "would_BTC SKU",
        "would_BTC Product Code",
        "would_BTC Supplier Stock",
        "would_Package Type",
        "would_Weight",
        "would_Service",
    ):
        if key in stats:
            print(f"  {key}: {stats[key]:,}")
    for line in samples:
        print(f"  e.g. {line}")

    if dry_run:
        print("  dry-run — no write")
        return dict(stats)

    bak = backup_file(path)
    print(f"  backup {bak}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print("  wrote", path)
    return dict(stats)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix Package Type/Weight/Service leaked into CL BTC columns.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
