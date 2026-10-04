"""Logo slot anchor / side-label helpers for back-print and banners."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

# Keep in sync with back_print_hint._ANCHORED_SUFFIX_RULES / LOCATION_LABEL.
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
LOCATION_LABEL = "LOCATION"


def strip_side_suffix_from_token(token: str) -> str:
    """Remove a trailing side segment (f/b/p/s1/s2/sl/sr/s)."""
    if not token:
        return token
    lower = token.lower()
    for _hyphenated, legacy, _label in _ANCHORED_SUFFIX_RULES:
        if lower.endswith(legacy):
            return token[: len(token) - len(legacy)]
    return token


def label_from_stem_after_anchor(stem: str, anchor_token: str) -> Optional[str]:
    """Map stem to Front/Back/Pocket/Sleeve (incl. left/right) after anchor_token."""
    if not stem or not anchor_token:
        return None
    s = stem.lower()
    a = anchor_token.lower()
    if not s.startswith(a):
        return None
    remainder = s[len(a) :]
    for hyphenated, legacy, label in _ANCHORED_SUFFIX_RULES:
        if remainder.startswith(hyphenated) or remainder == legacy:
            return label
    for _hyphenated, legacy, label in _ANCHORED_SUFFIX_RULES:
        if a.endswith(legacy):
            return label
    return None


def resolve_logo_anchor_for_slot(
    slot_index: int,
    row_series,
    *,
    fbpi_slots: List[Tuple[Path, str]],
    logo_design_tokens: Callable[..., List[str]],
) -> Optional[str]:
    """Logo/Design Image anchor for suffix detection on this logo slot."""
    tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
    if not tokens:
        return None
    if fbpi_slots:
        if slot_index == 0:
            return strip_side_suffix_from_token(tokens[0])
        fbpi_index = slot_index - 1
        if 0 <= fbpi_index < len(fbpi_slots):
            return strip_side_suffix_from_token(tokens[0])
        return None
    if slot_index < len(tokens):
        return tokens[slot_index]
    return None


def fbpi_side_label_for_slot(
    slot_index: int,
    fbpi_slots: List[Tuple[Path, str]],
    *,
    sides_start_at_zero: bool = False,
) -> Optional[str]:
    """Front/Back/… label from fbpi slot pairing, if any."""
    if not fbpi_slots:
        return None
    fbpi_index = slot_index if sides_start_at_zero else slot_index - 1
    if not sides_start_at_zero and slot_index < 1:
        return None
    if 0 <= fbpi_index < len(fbpi_slots):
        return fbpi_slots[fbpi_index][1]
    return None


def resolve_apparel_logo_anchor(
    row_series,
    *,
    logo_design_tokens: Callable[..., List[str]],
) -> Optional[str]:
    """First Logo/Design Image token (side suffix stripped) for apparel filenames."""
    tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
    if not tokens:
        return None
    return strip_side_suffix_from_token(tokens[0])


def label_for_logo_slot(
    stem: str,
    slot_index: int,
    row_series,
    *,
    fbpi_slots: List[Tuple[Path, str]],
    logo_design_tokens: Callable[..., List[str]],
) -> Optional[str]:
    """Banner label from anchored stem rules, with fbpi label fallback."""
    anchor = resolve_logo_anchor_for_slot(
        slot_index,
        row_series,
        fbpi_slots=fbpi_slots,
        logo_design_tokens=logo_design_tokens,
    )
    if anchor:
        label = label_from_stem_after_anchor(stem, anchor)
        if label:
            return label
    is_customised = str(row_series.get("Customise", "") or "").strip().lower() == "yes"
    sides_start_at_zero = bool(fbpi_slots) and not is_customised
    fallback = fbpi_side_label_for_slot(
        slot_index, fbpi_slots, sides_start_at_zero=sides_start_at_zero
    )
    if fallback == LOCATION_LABEL:
        return None
    return fallback


def logo_filename_indicates_back(
    img_path: Optional[Path],
    anchor_token: Optional[str] = None,
    *,
    fbpi_side_label: Optional[str] = None,
) -> bool:
    """True when the resolved logo stem has Back after anchor, or fbpi says Back."""
    if img_path is None:
        return False
    if anchor_token and label_from_stem_after_anchor(img_path.stem, anchor_token) == "Back":
        return True
    return fbpi_side_label == "Back"
