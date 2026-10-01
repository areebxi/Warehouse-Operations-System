"""Packing Input CSV write + report text."""
from __future__ import annotations

import csv
from collections import Counter
from datetime import date
from pathlib import Path

from shared import paths as wh

from grouping_parts import assign_inside_file
from grouping_shift import shift_file_token, shift_pair
from grouping_models import (
    CSV_FIELDNAMES,
    RESEND_FILE,
    UNMATCHED_FILE,
    Order,
    SortResult,
)



def input_date_folder(run: date) -> str:
    return run.strftime("%d-%m-%Y")


def next_open_shift(input_root: Path, run: date) -> tuple[str, str]:
    """Nth --run this calendar day (production later when SHIFT_PER_RUN is True)."""
    day = Path(input_root) / input_date_folder(run)
    n = 1
    while n < 20:
        slot, folder = shift_pair(n)
        if not any((day / folder).glob("*.csv")):
            return slot, folder
        n += 1
    return shift_pair(n)


def order_numbers_in_date_folder(input_root: Path, run: date) -> set[str]:
    """Order # already in any shift CSV for this run date (skip on a later run)."""
    day = Path(input_root) / input_date_folder(run)
    found: set[str] = set()
    if not day.is_dir():
        return found
    for csv_path in day.glob("*/*.csv"):
        try:
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    number = (row.get("Order #") or "").strip()
                    if number:
                        found.add(number)
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
    return found


def _csv_rows_for(order: Order) -> list[dict[str, str]]:
    if order.csv_rows:
        return list(order.csv_rows)
    tags = ", ".join(order.tag_names)
    return [
        {
            "Order #": order.number,
            "Ship By": order.ship_by_raw,
            "Quantity": str(ln.qty),
            "Item - Image URL": "",
            "Gift - Message": "",
            "Notes - From Buyer": "",
            "Item SKU": ln.sku,
            "Item Name": "",
            "Item - Options": "",
            "Recipient": "",
            "Tags": tags,
        }
        for ln in order.lines
    ]


def _orders_in_part_order(orders: list[Order]) -> list[Order]:
    parts = assign_inside_file(orders)
    return [o for p in parts for o in p.orders] if parts else list(orders)


def write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return path
    except PermissionError:
        # ponytail: Excel/Cursor lock — same fallback as CL csv-writes.
        fallback = path.with_name(path.stem + "_write_fallback" + path.suffix)
        with fallback.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return fallback


def write_process_csvs(
    result: SortResult,
    *,
    input_root: Path | None = None,
) -> list[Path]:
    """One CSV per process into this run's shift folder only. Other shifts stay put."""
    root = Path(input_root) if input_root else wh.packing_input_dir()
    date_folder = input_date_folder(result.run_date)
    folder = result.shift_folder
    (root / date_folder / folder).mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def dump(name: str, orders: list[Order]) -> None:
        ordered = _orders_in_part_order(orders)
        if not ordered:
            return
        path = root / date_folder / folder / f"{name}.csv"
        written.append(
            write_csv(path, [row for order in ordered for row in _csv_rows_for(order)])
        )

    dump(RESEND_FILE, result.resend)
    dump(UNMATCHED_FILE, result.unmatched)
    for bin_ in result.bins:
        dump(bin_.process_name, bin_.orders)

    keep = {p.resolve() for p in written}
    shift_dir = root / date_folder / folder
    for old in shift_dir.glob("*.csv"):
        if old.resolve() in keep:
            continue
        try:
            old.unlink()
        except PermissionError:
            pass
    return written


