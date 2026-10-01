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


