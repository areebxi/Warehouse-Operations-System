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

def test_resend_1014_only_and_blank_shipby() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order("R1", "77989LG-M-T-BLK-M", tags=["1014-ALL-RESEND"], catalogs=cat),
            _order("R2", "77989LG-M-T-BLK-M", tags=["1015-ALL-RESEND MANUALLY DISPATCHED"], catalogs=cat),
            _order("B1", "77989LG-M-T-BLK-M", ship="", catalogs=cat),
            _order(
                "M1",
                "77989LG-M-T-BLK-M",
                ship="",
                store="Manual Orders",
                catalogs=cat,
            ),
            _order(
                "E1",
                "77989LG-M-T-BLK-M",
                ship="",
                store="Etsy Apparel Villa",
                catalogs=cat,
            ),
        ],
        RUN,
    )
    assert [o.number for o in r.resend] == ["R1"]
    # Blank ship-by → today for every store (not unmatched).
    assert all(o.unmatched_reason != "blank ship-by" for o in r.unmatched)
    assert all(o.number != "B1" for o in r.unmatched)
    assert all(o.number != "M1" for o in r.unmatched)
    assert all(o.number != "E1" for o in r.unmatched)
    numbered = {o.number for b in r.bins for o in b.orders}
    assert {"B1", "M1", "E1"} <= numbered
    names = {b.process_name for b in r.bins}
    assert any(n.startswith("B1-S1-PRINTED-") for n in names)
    assert "resend" not in names
    assert "RESEND" not in names
    assert "UNMATCHED" not in names


def test_skip_dtfocean_wp_store() -> None:
    from grouping import EXCLUDE_STORES, orders_from_ss

    cat = _cats()
    raw = [
        {
            "orderNumber": "33335",
            "shipByDate": "2026-09-24",
            "storeId": 1,
            "tagIds": [],
            "items": [{"sku": "DTF-Transfer-5M", "name": "Buy DTF Transfer", "quantity": 1}],
        }
    ]
    out, post, empty, skipped = orders_from_ss(
        raw, {}, {1: "DTFOcean.co.uk WP"}, cat
    )
    assert out == []
    assert skipped == 1
    assert post == 0 and empty == 0
    assert "dtfocean.co.uk wp" in EXCLUDE_STORES


