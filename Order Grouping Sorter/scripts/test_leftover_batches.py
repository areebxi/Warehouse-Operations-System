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

import shared.paths as wh
from grouping_models import LineAttrs, Order, ProcessBin, SortResult
from leftover_batches import LEFTOVER_HEADER, write_leftover_batches_csv
from test_grouping_fixtures import RUN, _cats, _order
from grouping import FIXED_BATCH_CODES, group_orders


def _fake_leftover_result() -> SortResult:
    order = Order(
        number="H1",
        ship_by_raw=RUN.isoformat(),
        ship_by=RUN,
        tag_names=[],
        store_name="Amazon UK",
        lines=[LineAttrs(sku="X-M-H-BLK-M", qty=1, finish="printed", source="own")],
    )
    slots = [
        "printed",
        "own",
        "x",
        "non-prime",
        "dtf",
        "readymade",
        "x",
        "x",
        "x",
        "supplier_on_demand",
        "x",
        "x",
    ]
    bin_ = ProcessBin(
        shift_slot="1st",
        shift_folder="1st Shift",
        process_name="B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1",
        orders=[order],
        floor_code="B1",
        group_slots=slots,
        ship_by_slot="today",
    )
    return SortResult(
        run_date=RUN,
        skipped_post=0,
        empty_skipped=0,
        resend=[],
        unmatched=[],
        held=[],
        bins=[bin_],
        pool_orders=1,
    )


def test_leftover_default_path_under_logs() -> None:
    p = wh.sorter_leftover_batches_path(RUN)
    assert p == wh.sorter_logs_dir() / "leftover_batches" / f"{RUN.isoformat()}.csv"


def test_leftover_csv_records_criteria() -> None:
    dest = SCRIPTS / "_tmp_leftover_test"
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{RUN.isoformat()}.csv"
    r = _fake_leftover_result()
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
    test_leftover_default_path_under_logs()
    test_leftover_csv_records_criteria()
    test_fixed_batch_not_in_leftover_csv()
    print("test_leftover_batches: ok")
