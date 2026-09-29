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
    "B5500", "B3500", "B1050", "B10", "B70", "B3100", "B3600", "B3700", "B40",
    "B8050", "B8000", "B90", "B80", "B4000", "B100",
    "B5080", "B1080", "B5000", "B1000", "B2400", "B2300",
]


def test_table_loads() -> None:
    with wh.sorter_fixed_batches_path().open(encoding="utf-8-sig", newline="") as f:
        raw = list(csv.reader(f))
    assert all(len(r) == len(raw[0]) for r in raw), "ragged fixed_batches.csv row"
    rows = fixed_batch_table()
    assert [r.batch_code for r in rows] == EXPECTED_ORDER
    assert fixed_batch_codes() == set(EXPECTED_ORDER)
    assert {10, 2300, 2400, 8050} <= reserved_batch_nums()
    assert 8060 not in reserved_batch_nums() and 1 not in reserved_batch_nums()
    by = {r.batch_code: r for r in rows}
    assert by["B5500"].sku_contains == "179975LG" and by["B5500"].item_name_contains == "Dancing Queen"
    assert by["B10"].destination == "international"
    # 2026-09-29: t-shirt rows have no SKU include list; catalog ss_fotl + exclusions only.
    for code in ("B100", "B8000", "B80", "B4000", "B8050", "B90"):
        assert by[code].product_type == "ss_fotl" and by[code].sku_contains == "x", code
    assert by["B100"].sku_not_contains == "sticker;-Yes;-SS-;-H-;IronOn"
    assert by["B4000"].sku_not_contains == "sticker;-SS-;-H-;IronOn"
    assert by["B4000"].item_name_not_contains == "Glow In The Dark;Dancing Queen"
    # -Yes / Personali / Custom mark personalised: excluded only on ready-made rows.
    for code in ("B8050", "B90", "B4000", "B5080", "B5000"):
        assert "-yes" not in by[code].sku_not_contains.casefold(), code
        assert "personali" not in by[code].item_name_not_contains.casefold(), code
    for code in ("B8000", "B80", "B100", "B1080", "B1000"):
        assert "-yes" in by[code].sku_not_contains.casefold(), code
    assert by["B1000"].product_type == "iron_on" and by["B1000"].shipping_service == "any"


if __name__ == "__main__":
    test_table_loads()
    print("ok")
