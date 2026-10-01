from __future__ import annotations
import csv
import json
import re
from pathlib import Path
from app_paths import APP_ROOT, DATA_DIR, data_path
from stock_resolver import NOT_FOUND_STATUSES, STATUS_NOT_FOUND

def collect_not_found_skus() -> tuple[set[tuple[str, str]], list[Path], list[str]]:
    pairs: set[tuple[str, str]] = set()
    files: list[Path] = []
    warnings: list[str] = []

    for issue_path in _iter_not_found_source_files():
        parsed = _parse_issue_file(issue_path)
        if not parsed:
            warnings.append(f"Skipped (unexpected name): {issue_path}")
            continue

        tag_id, stamp = parsed
        is_stock_issues = bool(STOCK_ISSUES_RE.search(issue_path.name))
        detailed_path, json_path = _find_paired_files(issue_path, stamp, tag_id)
        if not detailed_path and not json_path:
            warnings.append(f"No tag order file for: {issue_path.name}")
            continue

        order_skus: dict[str, list[str]] = {}
        if json_path:
            order_skus = _load_order_skus_from_json(json_path)
        elif detailed_path:
            order_skus = _load_order_skus_from_detailed(detailed_path)

        files.append(issue_path)
        with _open_csv(issue_path) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not _row_is_not_found(row, is_stock_issues):
                    continue
                order_number = str(row.get("Order") or "").strip()
                complete_sku = str(row.get("Complete SKU") or "").strip()
                effective_item_sku = str(row.get("Item SKU") or "").strip()
                if not order_number:
                    continue
                if not complete_sku and not effective_item_sku:
                    continue

                skus_for_order = order_skus.get(order_number, [])
                shipstation_sku = _pick_shipstation_sku(
                    skus_for_order, effective_item_sku, complete_sku
                )
                if not shipstation_sku:
                    warnings.append(
                        f"No ShipStation SKU for order {order_number} "
                        f"(item {effective_item_sku or complete_sku}) in {issue_path.name}"
                    )
                    continue

                pairs.add(_to_row(shipstation_sku))

    return pairs, files, warnings
