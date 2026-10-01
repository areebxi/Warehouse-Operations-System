"""Normalize packing-list rows and PDF slip enrichment."""
from __future__ import annotations

import csv

from stock_resolver import NOT_FOUND_STATUSES
from run_packs import _pack_key


def normalize_packing_rows(in_stock_items):
    """Normalize in-stock rows to packing list CSV format (11 columns)."""
    normalized_rows = []
    for row in in_stock_items:
        # Not-found issue rows may include Status as a 10th field.
        if len(row) == 10 and str(row[9]) in NOT_FOUND_STATUSES:
            row = row[:9]
        if len(row) == 8:
            order_number, recipient_name, quantity, sku, tag_id, stock_level, pno, marketplace = row
            normalized_rows.append(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    sku,
                    "",
                    tag_id,
                    stock_level,
                    "",
                    "",
                    pno,
                    marketplace,
                ]
            )
        elif len(row) == 11:
            normalized_rows.append(row)
        elif len(row) == 10:
            normalized_rows.append(list(row) + [""])
        elif len(row) == 9:
            (
                order_number,
                recipient_name,
                quantity,
                item_sku,
                complete_sku,
                stock_id,
                tag_id,
                stock_level,
                pno,
            ) = row
            packing_sku = stock_id if stock_id else item_sku
            normalized_rows.append(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    packing_sku,
                    "",
                    tag_id,
                    stock_level,
                    "",
                    "",
                    pno,
                    complete_sku,
                ]
            )
        elif len(row) == 7:
            order_number, recipient_name, quantity, sku, tag_id, stock_level, pno = row
            normalized_rows.append(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    sku,
                    "",
                    tag_id,
                    stock_level,
                    "",
                    "",
                    pno,
                    "",
                ]
            )
        else:
            normalized_rows.append(row)
    return normalized_rows


def rows_for_pdf_slips(
    in_stock_items,
    out_of_stock_items=None,
    not_found_items=None,
    packs_map=None,
    pack_names_map=None,
):
    """Packing-slip PDF rows for EDI-eligible (in-stock) orders.

    Callers should pass only in_stock_items (same set as the EDI file).
    Optional OOS / not-found args are kept for compatibility but are unused when
    empty. Pack Components are rehydrated from Packs Database when missing.
    """
    issue_rows = list(out_of_stock_items or []) + list(not_found_items or [])
    rows = normalize_packing_rows((in_stock_items or []) + issue_rows)
    if not packs_map:
        return rows

    enriched = []
    for row in rows:
        if len(row) < 11:
            enriched.append(row)
            continue
        row = list(row)
        components_val = str(row[7] or "").strip()
        if not components_val:
            pack_key = _pack_key(str(row[3] or ""))
            comps = packs_map.get(pack_key) or []
            if comps:
                row[7] = ",".join(str(c.get("sku", "") or "") for c in comps)
                row[8] = ",".join(str(c.get("colour", "") or "") for c in comps)
                if not str(row[4] or "").strip() and pack_names_map:
                    row[4] = pack_names_map.get(pack_key, "") or ""
        enriched.append(row)
    return enriched


def write_packing_list_csv(filename: str, in_stock_items) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Order",
                "Recipient",
                "Quantity",
                "Item SKU",
                "Pack Name",
                "Tag",
                "Stock Level",
                "Components",
                "Component Colours",
                "Process No",
                "Marketplace SKU",
            ]
        )
        writer.writerows(normalize_packing_rows(in_stock_items))
