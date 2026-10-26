from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# Path bootstrap + fixtures + grouping API live in test_grouping_fixtures.
from test_grouping_fixtures import (  # noqa: F401
    FIXED_BATCH_CODES,
    PERSONALISED_READY_TAG,
    RUN,
    Catalogs,
    Order,
    _cats,
    _cl_row,
    _fotl_cats,
    _gildan_tee_cats,
    _iron_cats,
    _order,
    _packs_row,
    _plain_row,
    _ready,
    _sweatshirt_cats,
    attrs_for_sku,
    finish_for_sku,
    group_orders,
    next_open_shift,
    next_plain_batch_codes,
    order_numbers_in_date_folder,
    six_field_core,
    slotify,
    write_process_csvs,
)

def test_second_run_uses_s2_filename() -> None:
    cat = _cats()
    r = group_orders(
        [_order("G1", "77989LG-M-T-BLK-M", catalogs=cat)],
        RUN,
        shift_slot="2nd",
        shift_folder="2nd Shift",
    )
    assert r.bins[0].process_name == "B1-S2-PRINTED-2-SUPPLY ON DEMAND-R-1"
    assert r.bins[0].shift_folder == "2nd Shift"


def test_next_open_shift_and_written_order_numbers() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        root = Path(td)
        assert next_open_shift(root, RUN) == ("1st", "1st Shift")
        first = root / "11-09-2026" / "1st Shift"
        first.mkdir(parents=True)
        (first / "x.csv").write_text("Order #\nZ1\n", encoding="utf-8")
        assert next_open_shift(root, RUN) == ("2nd", "2nd Shift")
        assert order_numbers_in_date_folder(root, RUN) == {"Z1"}


def test_sort_does_not_skip_earlier_shift_by_default() -> None:
    """CLI must not pass exclude_order_numbers (locked 2026-10-14)."""
    from grouping_bins import sort_raw_orders

    cat = _cats()
    raw = [
        {
            "orderNumber": "KEEP1",
            "orderId": 1,
            "orderStatus": "awaiting_shipment",
            "shipByDate": "2026-09-11",
            "advancedOptions": {"storeId": 1},
            "tagIds": [],
            "items": [{"sku": "77989LG-M-T-BLK-M", "quantity": 1, "name": "t"}],
        }
    ]
    r = sort_raw_orders(
        raw,
        catalogs=cat,
        tag_id_to_name={},
        store_id_to_name={1: "Test"},
        run_date=RUN,
        shift_slot="3rd",
        shift_folder="3rd Shift",
        exclude_order_numbers={"KEEP1"},
    )
    assert r.skipped_already_written == 1
    r2 = sort_raw_orders(
        raw,
        catalogs=cat,
        tag_id_to_name={},
        store_id_to_name={1: "Test"},
        run_date=RUN,
        shift_slot="3rd",
        shift_folder="3rd Shift",
    )
    assert r2.skipped_already_written == 0
    assert any(o.number == "KEEP1" for b in r2.bins for o in b.orders)


def test_third_shift_leaves_future_ship_by() -> None:
    def orders() -> list[Order]:
        cat = _cats()
        return [
            _order("DUE", "77989LG-M-T-BLK-M", ship="2026-09-11", catalogs=cat),
            _order(
                "DUER", "77989LG-M-T-BLK-M", ship="2026-09-11",
                tags=[PERSONALISED_READY_TAG], catalogs=cat,
            ),
            _order("LATE", "77989LG-M-T-BLK-M", ship="2026-09-10", catalogs=cat),
            _order("BLANK", "77989LG-M-T-BLK-M", ship="", catalogs=cat),
            _order("FUT", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat),
            _order(
                "READY", "77989LG-M-T-BLK-M", ship="2026-09-20",
                tags=[PERSONALISED_READY_TAG], catalogs=cat,
            ),
        ]

    third = group_orders(orders(), RUN, shift_slot="3rd", shift_folder="3rd Shift")
    got = {o.number for b in third.bins for o in b.orders}
    assert got == {"DUE", "DUER", "LATE", "BLANK", "READY"}
    assert third.skipped_future == 1
    fourth = group_orders(orders(), RUN, shift_slot="4th", shift_folder="4th Shift")
    assert fourth.skipped_future == 1
    second = group_orders(orders(), RUN, shift_slot="2nd", shift_folder="2nd Shift")
    got2 = {o.number for b in second.bins for o in b.orders}
    assert {"DUE", "DUER", "FUT"} <= got2
    assert second.skipped_future == 0


