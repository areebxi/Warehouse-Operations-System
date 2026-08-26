"""Unit tests for ShipStation order flattening / path helpers."""

from pathlib import Path

from scripts.pipeline_shipstation.orders_to_csv import (
    input_csv_path_for_batch,
    orders_to_rows,
)


def test_orders_to_rows_skips_discount_and_adjustment():
    orders = [
        {
            "orderNumber": "ORD-1",
            "shipByDate": "2026-07-28T00:00:00.0000000",
            "giftMessage": "Happy!",
            "customerNotes": "Ship soon please",
            "tagIds": [10, 20],
            "shipTo": {"name": "Alice"},
            "items": [
                {
                    "sku": "SKU-1",
                    "name": "Tee",
                    "quantity": 2,
                    "imageUrl": "http://img",
                    "options": [{"name": "Size", "value": "L"}],
                    "adjustment": False,
                },
                {
                    "sku": "DISC",
                    "name": "Order Discount",
                    "quantity": 1,
                    "adjustment": False,
                },
                {
                    "sku": "ADJ",
                    "name": "Adjustment",
                    "quantity": 1,
                    "adjustment": True,
                },
            ],
        }
    ]
    rows = orders_to_rows(orders, {10: "Batch 100", 20: "Amazon Prime Order"})
    assert len(rows) == 1
    assert rows[0]["Order #"] == "ORD-1"
    assert rows[0]["Quantity"] == "2"
    assert rows[0]["Item SKU"] == "SKU-1"
    assert rows[0]["Item - Options"] == "Size: L"
    assert rows[0]["Recipient"] == "Alice"
    assert rows[0]["Gift - Message"] == "Happy!"
    assert rows[0]["Notes - From Buyer"] == "Ship soon please"
    assert rows[0]["Tags"] == "Batch 100, Amazon Prime Order"


def test_orders_to_rows_maps_customer_notes():
    orders = [
        {
            "orderNumber": "ORD-N",
            "customerNotes": "Birthday gift",
            "tagIds": [10],
            "shipTo": {"name": "Bob"},
            "items": [{"sku": "S1", "name": "Tee", "quantity": 1}],
        }
    ]
    rows = orders_to_rows(orders, {10: "Batch 100"})
    assert rows[0]["Notes - From Buyer"] == "Birthday gift"


def test_orders_to_rows_skips_post_order_designs_tag():
    orders = [
        {
            "orderNumber": "KEEP",
            "tagIds": [10],
            "shipTo": {"name": "A"},
            "items": [{"sku": "S1", "name": "Tee", "quantity": 1}],
        },
        {
            "orderNumber": "SKIP",
            "tagIds": [10, 99],
            "shipTo": {"name": "B"},
            "items": [{"sku": "S2", "name": "Hoodie", "quantity": 1}],
        },
    ]
    rows = orders_to_rows(
        orders,
        {10: "Batch 100", 99: "post-order-designs"},
    )
    assert len(rows) == 1
    assert rows[0]["Order #"] == "KEEP"


def test_input_csv_path_uses_shift_subdir(tmp_path: Path):
    path = input_csv_path_for_batch(
        "28-07-2026", "1st", "100", input_root=tmp_path
    )
    assert path == tmp_path / "28-07-2026" / "1st Shift" / "100.csv"
