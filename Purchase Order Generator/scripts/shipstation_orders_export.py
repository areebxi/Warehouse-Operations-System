"""CSV/JSON export helpers for PO ShipStation orders."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from typing import Dict, List

from shipstation_orders_csv_fields import CSV_FIELDNAMES
from shipstation_orders_csv_flatten import flatten_order_for_csv
from shipstation_orders_item import item_fields_for_csv


def export_orders_to_csv(orders: List[Dict], filename: str = None) -> str:
    """
    Export orders to CSV in the detailed format matching csv1.csv.

    Multi-SKU orders write one row per line item (order columns repeated).
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"awaiting_dispatch_orders_{timestamp}.csv"

    if not orders:
        print("No orders to export")
        return None

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()

        for order in orders:
            flattened_order = flatten_order_for_csv(order)
            items = order.get("items") or []
            if not items:
                flattened_order.update(item_fields_for_csv(None))
                writer.writerow(flattened_order)
                continue

            for item in items:
                row = dict(flattened_order)
                row.update(item_fields_for_csv(item or {}))
                writer.writerow(row)

    print(f"Orders exported to {filename}")
    return filename


def export_orders_to_json(orders: List[Dict], filename: str = None) -> str:
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"awaiting_dispatch_orders_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as jsonfile:
        json.dump(orders, jsonfile, indent=2, ensure_ascii=False, default=str)

    print(f"Orders exported to {filename}")
    return filename
