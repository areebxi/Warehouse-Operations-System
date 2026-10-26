"""Seed Areeb CL rows for awaiting_shipment catalog-miss SKUs.

  python "Order Grouping Sorter/scripts/seed_catalog_misses.py"
  python "Order Grouping Sorter/scripts/seed_catalog_misses.py --dry-run"

Uses the sorter finish gate. Appends only via Custom Label add_labels
(peer / definite supplier; no guessing). Does not write Packing Input.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
APP = SCRIPTS.parent
ROOT = APP.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shared import paths as wh  # noqa: E402
from shared.shipstation import ShipStationClient  # noqa: E402

from catalogs import load_catalogs  # noqa: E402
from grouping_intake import orders_from_ss  # noqa: E402
from grouping_models import Order  # noqa: E402

ADD_LABELS = ROOT / "Custom Label Database" / "scripts" / "add_labels.py"


def catalog_miss_skus(orders: list[Order]) -> list[str]:
    """Unique Item SKUs with no finish (same gate as sorter unmatched)."""
    seen: set[str] = set()
    out: list[str] = []
    for order in orders:
        for line in order.lines:
            if line.finish is not None:
                continue
            sku = (line.sku or "").strip()
            if not sku:
                continue
            key = sku.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(sku)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List catalog-miss SKUs; do not call add_labels",
    )
    args = parser.parse_args(argv)

    print("Loading catalogs (read-only)...")
    catalogs = load_catalogs()
    client = ShipStationClient(log=print)
    print("Fetching ShipStation stores / tags / awaiting_shipment...")
    stores = client.list_stores()
    tags = client.list_tags()
    raw = client.list_orders(order_status="awaiting_shipment")
    store_id_to_name = {int(s["storeId"]): str(s.get("storeName") or "") for s in stores}
    tag_id_to_name = {int(t["tagId"]): str(t.get("name") or "") for t in tags}
    orders, *_skip = orders_from_ss(raw, tag_id_to_name, store_id_to_name, catalogs)
    skus = catalog_miss_skus(orders)
    print(f"catalog-miss SKUs={len(skus)}  orders={len(orders)}")
    for sku in skus[:40]:
        print(f"  {sku}")
    if len(skus) > 40:
        print(f"  ... +{len(skus) - 40} more")
    if not skus:
        print("Nothing to seed.")
        return 0
    if args.dry_run:
        print("Dry-run: no add_labels.")
        return 0

    areeb = wh.cl_areeb_csv_path()
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        delete=False,
    ) as handle:
        handle.write("\n".join(skus) + "\n")
        skus_path = Path(handle.name)
    try:
        cmd = [
            sys.executable,
            str(ADD_LABELS),
            "--csv",
            str(areeb),
            "--skus-file",
            str(skus_path),
        ]
        print("Running:", " ".join(cmd), flush=True)
        completed = subprocess.run(cmd, cwd=str(ROOT), check=False)
    finally:
        skus_path.unlink(missing_ok=True)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
