"""Order Grouping Sorter.

  python "Order Grouping Sorter/scripts/run_sorter.py"
  python "Order Grouping Sorter/scripts/run_sorter.py" --run-date 2026-09-11
  python "Order Grouping Sorter/scripts/run_sorter.py" --run
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
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
from grouping import SHIFT_PER_RUN, format_report, next_open_shift, order_numbers_in_date_folder, sort_raw_orders, write_process_csvs  # noqa: E402
from leftover_batches import write_leftover_batches_csv  # noqa: E402


def _parse_run_date(raw: str | None) -> date:
    if not raw:
        return date.today()
    return date.fromisoformat(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Order Grouping Sorter")
    parser.add_argument("--run-date", help="YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Write one CSV per process into Packing Input",
    )
    args = parser.parse_args(argv)

    run_date = _parse_run_date(args.run_date)
    mode = "run" if args.run else "dry-run"
    print(f"Loading catalogs (read-only) for {mode} {run_date.isoformat()}...")
    catalogs = load_catalogs()
    print(
        f"  CL={len(catalogs.cl):,}  Plain={len(catalogs.plain):,}  Packs={len(catalogs.packs):,}"
    )

    def log(msg: str) -> None:
        print(msg)

    client = ShipStationClient(log=log)
    print("Fetching ShipStation stores / tags / awaiting_shipment...")
    stores = client.list_stores()
    tags = client.list_tags()
    orders = client.list_orders(order_status="awaiting_shipment")
    store_id_to_name = {int(s["storeId"]): str(s.get("storeName") or "") for s in stores}
    tag_id_to_name = {int(t["tagId"]): str(t.get("name") or "") for t in tags}

    input_root = wh.packing_input_dir()
    if SHIFT_PER_RUN:
        shift_slot, shift_folder = next_open_shift(input_root, run_date)
        already = order_numbers_in_date_folder(input_root, run_date)
    else:
        # Testing: every --run rewrites 1st Shift. Production later turns SHIFT_PER_RUN on.
        shift_slot, shift_folder = "1st", "1st Shift"
        already = set()
    result = sort_raw_orders(
        orders,
        catalogs=catalogs,
        tag_id_to_name=tag_id_to_name,
        store_id_to_name=store_id_to_name,
        run_date=run_date,
        shift_slot=shift_slot,
        shift_folder=shift_folder,
        exclude_order_numbers=already,
    )
    written = write_process_csvs(result) if args.run else None
    leftover_path = write_leftover_batches_csv(result)
    report = format_report(result, written=written)
    print(report, end="")
    print(f"Leftover batches CSV: {leftover_path}")

    logs_dir = wh.sorter_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = logs_dir / f"{mode}_{stamp}.txt"
    out.write_text(report, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
