"""Public re-exports so `from add_labels import …` keeps working for tests."""
from __future__ import annotations

from fill_from_seeds import hyphen_tshirt_in_slug

from add_labels_parse import (
    RE_ACRYLIC_SIZE,
    RE_AMZ_SIZE_CODE,
    RE_BAG_COLOUR,
    RE_BAG_SIZE_YES,
    RE_C800T_AGE,
    RE_GILDAN_5000,
    RE_IRONON,
    RE_TRANSFER,
    RE_WAREHOUSE_GARMENT,
    SEED_COLS,
    _ACRYLIC_PAPER,
    _BAG_COLOUR,
    _WAREHOUSE_GA,
    _age_to_size,
    _sticker_mm,
    _sticker_size,
    label_from_input,
)
from add_labels_peer_keys import _alias_shirt_colour_label, _peer_keys_for_label
from add_labels_peers import _collect_peers_for_labels, _scan_existing
from add_labels_peer_seed import _expand_all_spc
from add_labels_seeds import build_seed_rows
from add_labels_fill import fill_rows

__all__ = [
    "RE_ACRYLIC_SIZE",
    "RE_AMZ_SIZE_CODE",
    "RE_BAG_COLOUR",
    "RE_BAG_SIZE_YES",
    "RE_C800T_AGE",
    "RE_GILDAN_5000",
    "RE_IRONON",
    "RE_TRANSFER",
    "RE_WAREHOUSE_GARMENT",
    "SEED_COLS",
    "_ACRYLIC_PAPER",
    "_BAG_COLOUR",
    "_WAREHOUSE_GA",
    "_age_to_size",
    "_alias_shirt_colour_label",
    "_collect_peers_for_labels",
    "_expand_all_spc",
    "_peer_keys_for_label",
    "_scan_existing",
    "_sticker_mm",
    "_sticker_size",
    "build_seed_rows",
    "fill_rows",
    "hyphen_tshirt_in_slug",
    "label_from_input",
]
