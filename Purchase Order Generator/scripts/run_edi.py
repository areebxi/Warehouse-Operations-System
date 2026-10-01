"""EDI orders CSV writer for BTC."""
from __future__ import annotations

import csv
from datetime import datetime


def write_edi_orders_csv(filename: str, in_stock_items, process_no) -> None:
    current_dt = datetime.now()
    date_part = current_dt.strftime("%d-%m-%Y")
    order_id_suffix = f"{date_part}-EDI-DaataaDirect"
    order_id_value = f"{process_no}-{order_id_suffix}" if process_no else order_id_suffix

    # Plain UTF-8 (no BOM): BTC's importer treats BOM as part of the first header
    # name ("\ufeffstock-id"), so stock-id is not recognized.
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "stock-id",
                "order-id",
                "quantity-purchased",
                "product-name",
                "recipient-name",
                "sku",
                "ship-address-1",
                "ship-address-2",
                "ship-address-3",
                "ship-city",
                "ship-state",
                "ship-postal-code",
                "ship-country",
                "collection",
                "plain-cover",
                "delivery-tracking-email",
                "delivery-tracking-sms",
                "line-note",
            ]
        )

        for item in in_stock_items:
            if len(item) == 8:
                _order_number, _recipient, quantity, sku, _tag, _level, pno, _marketplace = item
                component_list = []
            elif len(item) >= 10:
                (
                    _order_number,
                    _recipient,
                    quantity,
                    sku,
                    _pack_name,
                    _tag,
                    _level,
                    components_joined,
                    _colours,
                    pno,
                    *_rest,
                ) = item
                component_list = [c for c in (components_joined or "").split(",") if c]
            else:
                _order_number, _recipient, quantity, sku, _tag, _level, pno = item[:7]
                component_list = []

            target_skus = component_list if component_list else [sku]
            for target_sku in target_skus:
                if not target_sku:
                    continue
                writer.writerow(
                    [
                        target_sku,
                        order_id_value,
                        quantity,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "GB",
                        "1",
                        "",
                        "",
                        "",
                        "",
                    ]
                )
