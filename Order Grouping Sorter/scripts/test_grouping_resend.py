"""Resend fixed batches B9040–B9200. Locked 2026-10-18."""
from __future__ import annotations

from test_grouping_fixtures import (
    RUN,
    Catalogs,
    _cats,
    _fotl_cats,
    _gildan_tee_cats,
    _iron_cats,
    _order,
    _sweatshirt_cats,
    group_orders,
)

RESEND = ["1014-ALL-RESEND"]


def _code(number: str, sku: str, catalogs: Catalogs) -> str:
    r = group_orders([_order(number, sku, tags=RESEND, catalogs=catalogs)], RUN)
    assert not r.held and not r.resend, (number, r.held, r.resend)
    return next(b.floor_code for b in r.bins for o in b.orders if o.number == number)


def test_resend_fixed_batches() -> None:
    assert _code("G", "77989LG-M-T-BLK-M", _gildan_tee_cats()) == "B9040"
    assert _code("GP", "77989LG-M-T-BLK-M", _gildan_tee_cats(**{"Customise": "Yes"})) == "B9040"
    assert _code("R", "1-M-T-WHT-M", _fotl_cats()) == "B9000"
    assert _code("PL", "1243-1", _cats()) == "B9000"
    assert _code("P", "1-M-T-WHT-M", _fotl_cats(**{"Customise": "Yes"})) == "B9050"
    assert _code("IO", "190867LG-DTF-IronOn-A4", _iron_cats()) == "B9100"
    assert _code("IP", "190867LG-DTF-IronOn-A4", _iron_cats(customise="Yes")) == "B9150"
    assert _code("SW", "1-M-SS-BLK-M", _sweatshirt_cats()) == "B9200"
    missed = group_orders([_order("U", "NOPE-UNKNOWN", tags=RESEND, catalogs=_cats())], RUN)
    assert [o.number for o in missed.resend] == ["U"]
    assert not missed.bins
