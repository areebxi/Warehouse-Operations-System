"""ponytail: fixed_batches.csv — fails if table missing or codes drift from locks."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
sys.path[:0] = [str(ROOT), str(SCRIPTS)]

import shared.paths as wh
from fixed_batches import clear_fixed_batch_cache, fixed_batch_codes, fixed_batch_table, reserved_batch_nums

clear_fixed_batch_cache()

# Locked priority (first match wins), supervisor 2026-09-28.
EXPECTED_ORDER = [
    "B9000", "B9050", "B9040", "B9100", "B9150", "B9200", "B10", "B700",
    "B5500", "B3500", "B1050", "B6000", "B6010", "B6020", "B6030", "B6050", "B6060", "B70",
    "B3150", "B3100", "B3650", "B3600", "B3750", "B3700", "B40",
    "B8050", "B8000", "B90", "B80", "B4000", "B4050", "B100", "B50",
    "B5080", "B1080", "B5000", "B1000", "B2350", "B2400", "B2300", "B7000", "B3000",
]


def test_table_loads() -> None:
    with wh.sorter_fixed_batches_path().open(encoding="utf-8-sig", newline="") as f:
        raw = list(csv.reader(f))
    assert all(len(r) == len(raw[0]) for r in raw), "ragged fixed_batches.csv row"
    rows = fixed_batch_table()
    assert [r.batch_code for r in rows] == EXPECTED_ORDER
    assert fixed_batch_codes() == set(EXPECTED_ORDER)
    assert {10, 50, 2300, 2400, 8050} <= reserved_batch_nums()
    assert 8060 not in reserved_batch_nums() and 1 not in reserved_batch_nums()
    by = {r.batch_code: r for r in rows}
    assert by["B5500"].sku_contains == "179975LG" and by["B5500"].item_name_contains == "Dancing Queen+Glitter"
    assert by["B6000"].sku_contains == "BG-Chinabag" and by["B6000"].product_finish == "plain"
    assert by["B6010"].sku_contains == "BG125" and by["B6010"].product_finish == "plain"
    assert by["B6020"].sku_contains == "BG-Chinabag" and by["B6020"].product_finish == "printed"
    assert by["B6020"].customised == "readymade" and by["B6020"].destination == "uk"
    assert by["B6030"].sku_contains == "BG125" and by["B6030"].customised == "readymade"
    assert by["B6050"].sku_contains == "BG-Chinabag" and by["B6050"].customised == "customised"
    assert by["B6060"].sku_contains == "BG125" and by["B6060"].customised == "customised"
    assert {6000, 6010, 6020, 6030, 6050, 6060} <= reserved_batch_nums()
    assert by["B10"].destination == "international"
    assert by["B10"].sku_not_contains == "x" and by["B10"].item_name_not_contains == "x"
    assert by["B700"].destination == by["B5500"].destination == by["B6000"].destination == "uk"
    # 2026-09-29: t-shirt rows have no SKU include list; catalog ss_fotl + exclusions only.
    for code in ("B100", "B50", "B8000", "B80", "B4000", "B8050", "B90"):
        assert by[code].product_type == "ss_fotl" and by[code].sku_contains == "x", code
    assert by["B100"].supply_method == "Warehouse Stock"
    assert by["B50"].supply_method == "Supplier On Demand"
    assert by["B100"].sku_not_contains == by["B50"].sku_not_contains == "sticker;-Yes;-SS-;-H-;IronOn"
    assert by["B4000"].sku_not_contains == "sticker;-SS-;-H-;IronOn"
    assert by["B4000"].item_name_not_contains == "Glow In The Dark;Dancing Queen+Glitter"
    # -Yes / Personali / Custom mark personalised: excluded only on ready-made rows.
    for code in ("B8050", "B90", "B4000", "B5080", "B5000"):
        assert "-yes" not in by[code].sku_not_contains.casefold(), code
        assert "personali" not in by[code].item_name_not_contains.casefold(), code
    for code in ("B8000", "B80", "B100", "B50", "B1080", "B1000"):
        assert "-yes" in by[code].sku_not_contains.casefold(), code
    assert by["B1000"].product_type == "iron_on" and by["B1000"].shipping_service == "any"
    assert by["B9040"].order_status == "resend" and by["B9040"].product_type == "gildan_tee"
    assert by["B9050"].product_type == "tee_not_gildan" and by["B9050"].customised == "customised"
    assert by["B9000"].product_type == "tee_not_gildan" and by["B9000"].customised == "not-customised"
    assert by["B40"].product_type == "gildan_any"
    assert by["B8000"].supply_method == "x" and by["B4050"].supply_method == "Supplier On Demand"
    assert by["B2350"].product_finish == "printed" and by["B2350"].supplier == "uneek clothing"
    assert by["B3100"].customised == "readymade" and by["B3150"].customised == "customised"
    assert by["B9150"].product_type == "iron_on" and by["B9150"].customised == "customised"
    assert by["B9100"].product_type == "iron_on" and by["B9100"].customised == "readymade"
    assert by["B9200"].order_status == "resend" and by["B9200"].product_type == "resend_other"
    assert {9000, 9040, 9050, 9100, 9150, 9200, 700} <= reserved_batch_nums()
    assert by["B700"].printing_method == "uv" and by["B700"].product_finish == "x"


if __name__ == "__main__":
    test_table_loads()
    print("ok")
