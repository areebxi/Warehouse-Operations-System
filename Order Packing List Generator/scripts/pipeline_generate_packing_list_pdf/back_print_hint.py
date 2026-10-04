"""Back-print detection for logo grid cells and suffix banner labels."""

from __future__ import annotations

from pipeline_generate_packing_list_pdf.back_print_hint_impl import (
    next_logo_slot_index,
    resolve_position_tokens_for_row,
    slot_is_back_print,
)
from pipeline_generate_packing_list_pdf.back_print_hint_labels import (
    fbpi_side_label_for_slot,
    label_for_logo_slot,
    label_from_stem_after_anchor,
    logo_filename_indicates_back,
    resolve_apparel_logo_anchor,
    resolve_logo_anchor_for_slot,
    strip_side_suffix_from_token,
)

# Longer sleeve tokens (s1/s2/sl/sr) must come before generic ``-s``.
_ANCHORED_SUFFIX_RULES: tuple[tuple[str, str, str], ...] = (
    ("-f-", "-f", "Front"),
    ("-b-", "-b", "Back"),
    ("-p-", "-p", "Pocket"),
    ("-s1-", "-s1", "Left Sleeve"),
    ("-s2-", "-s2", "Right Sleeve"),
    ("-sl-", "-sl", "Left Sleeve"),
    ("-sr-", "-sr", "Right Sleeve"),
    ("-s-", "-s", "Sleeve"),
)

FBPI_SIDE_SUFFIX_LOOKUP: tuple[tuple[str, str], ...] = (
    ("f", "Front"),
    ("b", "Back"),
    ("p", "Pocket"),
    ("s1", "Left Sleeve"),
    ("s2", "Right Sleeve"),
    ("sl", "Left Sleeve"),
    ("sr", "Right Sleeve"),
    ("s", "Sleeve"),
)

LOCATION_LABEL = "LOCATION"
FBPI_SIDE_LABELS = frozenset(label for _suffix, label in FBPI_SIDE_SUFFIX_LOOKUP)
BANNER_BLANK_LABELS = FBPI_SIDE_LABELS | {LOCATION_LABEL}

_FBPI_LABEL_TO_LETTER = {label: suffix for suffix, label in FBPI_SIDE_SUFFIX_LOOKUP}


def has_fbpi_side_files(fbpi_slots: list) -> bool:
    """True when Front/Back/Pocket/Sleeve files are present (not LOCATION-only)."""
    return any(label in FBPI_SIDE_LABELS for _path, label in fbpi_slots)


__all__ = [
    "BANNER_BLANK_LABELS",
    "FBPI_SIDE_LABELS",
    "FBPI_SIDE_SUFFIX_LOOKUP",
    "LOCATION_LABEL",
    "_ANCHORED_SUFFIX_RULES",
    "_FBPI_LABEL_TO_LETTER",
    "fbpi_side_label_for_slot",
    "has_fbpi_side_files",
    "label_for_logo_slot",
    "label_from_stem_after_anchor",
    "logo_filename_indicates_back",
    "next_logo_slot_index",
    "resolve_apparel_logo_anchor",
    "resolve_logo_anchor_for_slot",
    "resolve_position_tokens_for_row",
    "slot_is_back_print",
    "strip_side_suffix_from_token",
]
