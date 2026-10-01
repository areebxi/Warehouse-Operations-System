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

def test_blank_customise_is_readymade_not_unmatched() -> None:
    cat = _cats()
    r = group_orders([_order("C1", "77989LG-M-T-BLK-M", catalogs=cat)], RUN)
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"
    assert r.unmatched == []


def test_mixed_customised_majority_units_tie_readymade() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(),
            "m-t-wht-m": _cl_row(
                **{"Custom Label": "M-T-WHT-M", "Customise": "Yes"}
            ),
        }
    )
    majority_r = _order(
        "RWIN",
        "77989LG-M-T-BLK-M",
        catalogs=cat,
        extra_lines=[
            ("77989LG-M-T-BLK-M", 1),
            ("77989LG-M-T-BLK-M", 1),
            ("88000LG-M-T-WHT-M", 1),
        ],
    )
    r = group_orders([majority_r], RUN)
    assert r.unmatched == []
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"

    # 3 customised units vs 2 readymade lines — units, not line count.
    majority_p = _order(
        "PWIN",
        "88000LG-M-T-WHT-M",
        qty=3,
        catalogs=cat,
        tags=_ready(),
        extra_lines=[("77989LG-M-T-BLK-M", 1), ("77989LG-M-T-BLK-M", 1)],
    )
    r2 = group_orders([majority_p], RUN)
    assert r2.unmatched == []
    assert r2.held == []
    assert r2.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-P-1"

    tie = _order(
        "TIE",
        "77989LG-M-T-BLK-M",
        catalogs=cat,
        extra_lines=[("88000LG-M-T-WHT-M", 1)],
    )
    r3 = group_orders([tie], RUN)
    assert r3.unmatched == []
    assert r3.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"


def test_personalised_without_ready_tag_is_held() -> None:
    cat = _fotl_cats(**{"Customise": "Yes"})
    ready = _order("OK", "1-M-T-WHT-M", catalogs=cat, tags=_ready())
    waiting = _order("WAIT", "1-M-T-WHT-M", catalogs=cat)
    not_ready = _order(
        "NR",
        "1-M-T-WHT-M",
        catalogs=cat,
        tags=["1003-Personalised-Design-Not Ready"],
    )
    r = group_orders([ready, waiting, not_ready], RUN)
    assert {o.number for o in r.held} == {"WAIT", "NR"}
    assert all(o.unmatched_reason == "personalised design not ready" for o in r.held)
    numbered = {o.number for b in r.bins for o in b.orders}
    assert numbered == {"OK"}
    assert "WAIT" not in numbered
    assert r.unmatched == []


