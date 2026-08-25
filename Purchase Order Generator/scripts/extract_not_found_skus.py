"""Extract Basic SKU / Custom Label pairs from not-found issue files via tag order data."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from app_paths import APP_ROOT, DATA_DIR, data_path
from stock_resolver import NOT_FOUND_STATUSES, STATUS_NOT_FOUND

NOT_FOUND_RE = re.compile(r"sku_not_found_tag_(.+)_(\d{8}_\d{6})\.csv$", re.I)
STOCK_ISSUES_RE = re.compile(r"stock_issues_tag_(.+)_(\d{8}_\d{6})\.csv$", re.I)
_NOT_FOUND_STATUS_FOLDS = frozenset(s.casefold() for s in NOT_FOUND_STATUSES)


def _open_csv(path: Path):
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return open(path, encoding=encoding, newline="")
        except UnicodeDecodeError:
            continue
    return open(path, encoding="utf-8", errors="replace", newline="")


def _custom_label(shipstation_sku: str) -> str:
    sku = str(shipstation_sku or "").strip()
    if "-" in sku:
        return sku.split("-", 1)[1].strip()
    return ""


def _stock_id_part(sku: str) -> str:
    """Part before first dash — used only to match not-found Item SKU rows."""
    sku = str(sku or "").strip()
    if "-" in sku:
        return sku.split("-", 1)[0].strip()
    return sku


def _to_row(shipstation_sku: str) -> tuple[str, str]:
    sku = str(shipstation_sku or "").strip()
    if not sku:
        return "", ""
    return sku, _custom_label(sku)


def _find_paired_files(issue_path: Path, stamp: str, tag_id: str) -> tuple[Path | None, Path | None]:
    """Return (awaiting_detailed_csv, awaiting_orders_json) for the same run."""
    folder = issue_path.parent
    detailed = folder / f"tag_{tag_id}_awaiting_detailed_{stamp}.csv"
    orders_json = folder / f"tag_{tag_id}_awaiting_orders_{stamp}.json"
    if detailed.exists():
        return detailed, orders_json if orders_json.exists() else None
    return None, orders_json if orders_json.exists() else None


def _load_order_skus_from_json(json_path: Path) -> dict[str, list[str]]:
    with open(json_path, encoding="utf-8") as handle:
        orders = json.load(handle)
    by_order: dict[str, list[str]] = {}
    for order in orders:
        order_number = str(order.get("orderNumber", "")).strip()
        if not order_number:
            continue
        skus: list[str] = []
        for item in order.get("items") or []:
            sku = str(item.get("sku") or "").strip()
            if sku:
                skus.append(sku)
        if skus:
            by_order[order_number] = skus
    return by_order


def _load_order_skus_from_detailed(detailed_path: Path) -> dict[str, list[str]]:
    by_order: dict[str, list[str]] = {}
    with _open_csv(detailed_path) as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            order_number = str(row.get("orderNumber") or "").strip()
            if not order_number:
                continue
            sku = str(row.get("basic sku") or row.get("items 0 sku") or "").strip()
            if sku:
                by_order.setdefault(order_number, []).append(sku)
    return by_order


def _pick_shipstation_sku(
    order_skus: list[str],
    effective_item_sku: str,
    complete_sku: str = "",
) -> str | None:
    complete = str(complete_sku or "").strip()
    if complete:
        return complete
    if not order_skus:
        return None
    effective = str(effective_item_sku or "").strip()
    if effective:
        for sku in order_skus:
            sku = str(sku)
            if _stock_id_part(sku) == effective or sku.startswith(f"{effective}-"):
                return sku
        return None
    if len(order_skus) == 1:
        return order_skus[0]
    return None


def _iter_not_found_source_files() -> list[Path]:
    search_roots = [DATA_DIR, APP_ROOT / "Data", APP_ROOT / "output"]
    out_name = "sku_not_found_basic_and_custom_label.csv"
    found: list[Path] = []
    for base in search_roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("sku_not_found*.csv")):
            if path.name.lower() == out_name.lower():
                continue
            found.append(path)
        for path in sorted(base.rglob("stock_issues*.csv")):
            found.append(path)
    return found


def _parse_issue_file(path: Path) -> tuple[str, str] | None:
    """Return (tag_id, stamp) for legacy not-found or stock_issues files."""
    match = NOT_FOUND_RE.search(path.name)
    if match:
        return match.group(1), match.group(2)
    match = STOCK_ISSUES_RE.search(path.name)
    if match:
        return match.group(1), match.group(2)
    return None


def _row_is_not_found(row: dict, is_stock_issues: bool) -> bool:
    if not is_stock_issues:
        return True
    status = str(row.get("Status") or "").strip().casefold()
    return status in _NOT_FOUND_STATUS_FOLDS


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


def main() -> None:
    pairs, files, warnings = collect_not_found_skus()
    out_path = data_path("sku_not_found_basic_and_custom_label.csv")

    rows = sorted(pairs, key=lambda x: (x[0].lower(), x[1].lower()))
    with open(out_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL)
        writer.writerow(["Basic SKU", "Custom Label"])
        for basic_sku, custom_label in rows:
            writer.writerow([str(basic_sku), str(custom_label)])

    with_label = sum(1 for _, label in rows if label)
    print(f"Scanned {len(files)} not-found / stock-issues file(s)")
    print(f"Wrote {len(rows)} unique SKU(s) ({with_label} with custom label)")
    print(f"Output: {out_path}")
    if warnings:
        print(f"Warnings: {len(warnings)}")
        for line in warnings[:20]:
            print(f"  {line}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")


if __name__ == "__main__":
    main()
