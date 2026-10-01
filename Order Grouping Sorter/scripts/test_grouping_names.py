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

def test_six_field_filename_tokens() -> None:
    left = [
        "printed",
        "own",
        "x",
        "prime",
        "dtf",
        "customised",
        "x",
        "x",
        "x",
        slotify("Warehouse Stock"),
        "x",
        "x",
    ]
    assert six_field_core(left, "1st") == "S1-PRINTED-1-WAREHOUSE STOCK-P"
    left[0] = "plain"
    left[3] = "non-prime"
    left[5] = "x"
    left[9] = slotify("Supplier On Demand")
    assert six_field_core(left, "2nd") == "S2-PLAIN-2-SUPPLY ON DEMAND-R"


def test_priority_today_then_prime_then_as_made() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order("TN", "77989LG-M-T-BLK-M", catalogs=cat),
            _order("FN", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat),
            _order("TP", "77989LG-M-T-BLK-M", tags=["Amazon Prime Order"], catalogs=cat),
        ],
        RUN,
    )
    by = {o.number: b.process_name for b in r.bins for o in b.orders}
    assert by["TP"] == "B1-S1-PRINTED-1-SUPPLY ON DEMAND-R-1"
    assert by["TN"] == "B2-S1-PRINTED-2-SUPPLY ON DEMAND-R-2"
    assert by["FN"] == "B2-S1-PRINTED-2-SUPPLY ON DEMAND-R-2"


