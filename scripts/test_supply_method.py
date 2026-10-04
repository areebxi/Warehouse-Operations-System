"""ponytail: Supply Method lock — fails if FOTL tee / iron-on / Gildan routing drifts."""

from __future__ import annotations

from pathlib import Path

from scripts.test_supply_method_cl import (
    test_cl_colour_gate_and_body_suits,
    test_fotl_tees_are_warehouse,
    test_gildan_and_everything_else_on_demand,
    test_iron_on_and_sticker_in_house_on_cl_only,
    test_normalize_stock_type,
)
from scripts.test_supply_method_plain import ROOT, test_fotl_vest_is_not_warehouse, test_harvest_pack_name_is_not_a_vest, test_plain_and_packs_never_in_house

__all__ = [
    "ROOT",
    "test_cl_colour_gate_and_body_suits",
    "test_fotl_tees_are_warehouse",
    "test_fotl_vest_is_not_warehouse",
    "test_gildan_and_everything_else_on_demand",
    "test_harvest_pack_name_is_not_a_vest",
    "test_iron_on_and_sticker_in_house_on_cl_only",
    "test_normalize_stock_type",
    "test_plain_and_packs_never_in_house",
]

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    test_fotl_tees_are_warehouse()
    test_cl_colour_gate_and_body_suits()
    test_gildan_and_everything_else_on_demand()
    test_iron_on_and_sticker_in_house_on_cl_only()
    test_normalize_stock_type()
    test_fotl_vest_is_not_warehouse()
    test_harvest_pack_name_is_not_a_vest()
    test_plain_and_packs_never_in_house()
    print("ok")

