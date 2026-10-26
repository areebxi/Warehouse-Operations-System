"""Put a ShipStation shift tag on Order #s from packing CSVs.

  python "Order Grouping Sorter/scripts/tag_shift_orders.py" --shift 1st a.csv b.csv

Skips an order that already has the tag. Posts in parallel (8 workers).
Pauses when the rate-limit header says the window is nearly empty.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shared.shipstation import ShipStationClient, ShipStationError  # noqa: E402
from tag_shift_workers import pause_seconds, tag_all  # noqa: E402

SHIFT_TAG = {
    "1st": "001-1st Shift",
    "2nd": "002-2nd Shift",
    "3rd": "003-3rd Shift",
    "4th": "004-4th Shift",
    "5th": "005-5th Shift",
}


def order_numbers(paths: list[Path]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                number = (row.get("Order #") or "").strip()
                if number and number not in seen:
                    seen.add(number)
                    out.append(number)
    return out


def tag_id_for(tags: list[dict], shift: str) -> tuple[str, int]:
    name = SHIFT_TAG[shift]
    for tag in tags:
        if str(tag.get("name") or "") == name:
            return name, int(tag["tagId"])
    raise ShipStationError(f"ShipStation has no tag named {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tag orders in packing CSVs")
    parser.add_argument("--shift", required=True, choices=tuple(SHIFT_TAG))
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    numbers = order_numbers(args.files)
    client = ShipStationClient(log=print)
    _name, tag_id = tag_id_for(client.list_tags(), args.shift)
    by_number: dict[str, dict] = {}
    for order in client.list_orders(order_status="awaiting_shipment"):
        number = str(order.get("orderNumber") or "").strip()
        if number:
            by_number[number] = order
    todo: list[tuple[str, int]] = []
    already = missing = 0
    for number in numbers:
        order = by_number.get(number)
        if order is None:
            missing += 1
            print(f"missing {number}")
            continue
        tags = order.get("tagIds") or []
        if tag_id in tags or str(tag_id) in {str(t) for t in tags}:
            already += 1
            continue
        todo.append((number, int(order["orderId"])))
    print(
        f"{_name} id={tag_id}  orders={len(numbers)}  already={already}  "
        f"to_tag={len(todo)}  missing={missing}",
        flush=True,
    )
    creds = client.credentials
    ok, errors = tag_all(
        auth=(creds.api_key, creds.api_secret),
        base_url=creds.base_url,
        tag_id=tag_id,
        todo=todo,
        log=lambda m: print(m, flush=True),
    )
    print(
        f"done tagged={ok} already={already} missing={missing} failed={len(errors)}",
        flush=True,
    )
    return 1 if missing or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
