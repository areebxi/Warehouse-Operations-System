"""ponytail: leftover_batches CSV — fails if dated criteria shape drifts."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from catalogs import Catalogs
from grouping import FIXED_BATCH_CODES, group_orders
from leftover_batches import LEFTOVER_HEADER, write_leftover_batches_csv
from test_grouping import RUN, _cats, _order


def _hoodie_cats() -> Catalogs:
    """T-Shirt & Hoodie bundle stays leftover (B3600 is Hoodie / Zip Hoodie only)."""
    return Catalogs(
        cl={
            "m-h-blk-m": {
                "Custom Label": "M-H-BLK-M",
                "Supply Method": "Supplier On Demand",
                "Supplier Name": "BTC Activewear",
                "Printing Type": "DTF",
                "Customise": "",
                "Category (Areeb)": "Sweatshirts & Hoodies",
                "Product Type (Areeb)": "T-Shirt & Hoodie",
                "Product Style (Areeb)": "Standard",
                "Department (Areeb)": "Mens",
                "Brand": "Gildan",
                "Size": "M",
                "Colour": "Black",
            }
        },
        plain={},
        packs={},
    )


def test_leftover_csv_records_criteria() -> None:
    dest = SCRIPTS / "_tmp_leftover_test"
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{RUN.isoformat()}.csv"
    r = group_orders([_order("H1", "X-M-H-BLK-M", catalogs=_hoodie_cats())], RUN)
    assert all(b.floor_code not in FIXED_BATCH_CODES for b in r.bins if b.orders)
    out = write_leftover_batches_csv(r, path=path)
    assert out == path
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(csv.DictReader(path.open(encoding="utf-8", newline="")).fieldnames) == LEFTOVER_HEADER
    assert len(rows) == 1
    row = rows[0]
    assert row["batch_code"] == "B1"
    assert row["product-finish"] == "printed"
    assert row["order-source"] == "own"
    assert row["shipping-service"] == "non-prime"
    assert row["printing-method"] == "dtf"
    assert row["customised"] == "readymade"
    assert row["supply-method"] == "SUPPLY ON DEMAND"
    assert row["order-status"] == "awaiting_shipment"
    assert "filename=B1-S1-" in row["notes"]
    assert row["item-name-contains"] == "x"
    assert row["sku-contains"] == "x"


def test_fixed_batch_not_in_leftover_csv() -> None:
    dest = SCRIPTS / "_tmp_leftover_test"
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / "fixed_only.csv"
    r = group_orders([_order("F1", "77989LG-M-T-BLK-M", catalogs=_cats())], RUN)
    write_leftover_batches_csv(r, path=path)
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    codes = {row["batch_code"] for row in rows}
    assert codes.isdisjoint(FIXED_BATCH_CODES)


if __name__ == "__main__":
    test_leftover_csv_records_criteria()
    test_fixed_batch_not_in_leftover_csv()
    print("test_leftover_batches: ok")
