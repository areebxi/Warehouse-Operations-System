"""One fixed batch per order. Locked 2026-10-18."""
from __future__ import annotations

from test_grouping_fixtures import (
    RUN,
    Catalogs,
    Order,
    _cl_row,
    _fotl_cats,
    _gildan_tee_cats,
    _order,
    _ready,
    group_orders,
)
from grouping_fixed import fixed_batch_matches
from grouping_slots import _order_finish, left_slots

PRIME = ["amazon prime order"]


def _hits(order: Order) -> list[str]:
    order.finish = _order_finish(order) or ""
    slots = left_slots(order, order.finish) if order.finish else None
    order.left = slots or []
    return fixed_batch_matches(order, run=RUN) if order.left else []


def _one(order: Order, code: str) -> None:
    assert _hits(order) == [code], (order.number, _hits(order))


def test_one_fixed_batch_each() -> None:
    fotl = _fotl_cats()
    on_demand = _fotl_cats(**{"Stock_Type": "Supplier On Demand"})
    gildan = _gildan_tee_cats(**{"Stock_Type": "Supplier On Demand"})
    mixed = Catalogs(
        cl={
            "m-t-wht-m": fotl.cl["m-t-wht-m"],
            "m-t-gil-m": _cl_row(
                **{
                    "Custom_Label": "M-T-GIL-M",
                    "Brand": "Gildan",
                    "Stock_Type": "Supplier On Demand",
                    "Category (Areeb)": "T-Shirts",
                    "Product Type (Areeb)": "Short Sleeve T-Shirt",
                }
            ),
        }
    )
    uneek = Catalogs(
        cl={
            "uc604": _cl_row(
                **{
                    "Custom_Label": "UC604",
                    "Brand": "Uneek",
                    "Supplier_Name": "Uneek Clothing",
                    "Category (Areeb)": "Fleeces",
                    "Product Type (Areeb)": "Fleece",
                }
            )
        }
    )
    bag = Catalogs(
        cl={
            "tote-1": _cl_row(
                **{
                    "Custom_Label": "TOTE-1",
                    "Brand": "Westford Mill",
                    "Category (Areeb)": "Bags",
                    "Product Type (Areeb)": "Tote",
                }
            )
        }
    )
    queen = _order("DQ", "179975LG-M-T-WHT-M", catalogs=fotl, item_name="Dancing Queen Glitter Tee")
    plain_name = _order("DQN", "1-M-T-WHT-M", catalogs=fotl, item_name="Dancing Queen Tee")
    mixed_order = _order("MX", "1-M-T-WHT-M", catalogs=mixed, extra_lines=[("9LG-M-T-GIL-M", 1)])
    prime_od = _order("PR", "1-M-T-WHT-M", catalogs=on_demand, tags=PRIME)
    prime_g = _order("PG", "77989LG-M-T-BLK-M", catalogs=gildan, tags=PRIME)
    custom_od = _order(
        "CU", "1-M-T-WHT-M", catalogs=on_demand, item_name="Custom Kids Tee", tags=_ready()
    )
    _one(queen, "B5500")
    _one(plain_name, "B100")
    _one(mixed_order, "B40")
    _one(prime_od, "B8000")
    _one(prime_g, "B40")
    _one(custom_od, "B4050")
    _one(_order("UN", "9LG-UC604", catalogs=uneek), "B2350")
    _one(_order("BAG", "9LG-TOTE-1", catalogs=bag), "B3000")
    intl = _order("IE", "1-M-T-WHT-M", catalogs=fotl)
    intl.ship_country = "IE"
    _one(intl, "B10")


def test_b700_uv_peels_before_specials() -> None:
    uv = _fotl_cats(**{"Printing_Type": "UV"})
    tee = _hits(_order("UV", "1-M-T-WHT-M", catalogs=uv))
    assert tee[0] == "B700", tee
    queen = _hits(
        _order("UVQ", "179975LG-M-T-WHT-M", catalogs=uv, item_name="Dancing Queen Glitter Tee")
    )
    assert queen[0] == "B700" and "B5500" in queen, queen
    abroad_order = _order("UVI", "1-M-T-WHT-M", catalogs=uv)
    abroad_order.ship_country = "IE"
    abroad = _hits(abroad_order)
    assert abroad == ["B10"], abroad
    assert _hits(_order("DTF", "1-M-T-WHT-M", catalogs=_fotl_cats())) == ["B100"]
    resent = group_orders(
        [_order("UVR", "1-M-T-WHT-M", tags=["1014-ALL-RESEND"], catalogs=uv)], RUN
    )
    assert not resent.held and not resent.resend
    code = next(b.floor_code for b in resent.bins for o in b.orders if o.number == "UVR")
    assert code == "B9000", code
