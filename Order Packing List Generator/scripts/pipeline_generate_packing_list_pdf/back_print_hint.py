"""Back-print detection for logo grid cells and suffix banner labels."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.core_helpers import classify_position_token_impl

# (remainder prefix with trailing hyphen, legacy remainder, label)
_ANCHORED_SUFFIX_RULES: tuple[tuple[str, str, str], ...] = (
    ("-f-", "-f", "Front"),
    ("-b-", "-b", "Back"),
    ("-p-", "-p", "Pocket"),
    ("-s-", "-s", "Sleeve"),
)

FBPI_SIDE_SUFFIX_LOOKUP: tuple[tuple[str, str], ...] = (
    ("f", "Front"),
    ("b", "Back"),
    ("p", "Pocket"),
    ("s", "Sleeve"),
)

_FBPI_LABEL_TO_LETTER = {label: suffix for suffix, label in FBPI_SIDE_SUFFIX_LOOKUP}


def strip_side_suffix_from_token(token: str) -> str:
    """Remove a trailing ``-f`` / ``-b`` / ``-p`` / ``-s`` segment from a logo token."""
    if not token:
        return token
    lower = token.lower()
    for _hyphenated, legacy, _label in reversed(_ANCHORED_SUFFIX_RULES):
        if lower.endswith(legacy) and (len(lower) == len(legacy) or lower[len(lower) - len(legacy) - 1] == "-"):
            return token[: len(token) - len(legacy)]
    return token


def label_from_stem_after_anchor(stem: str, anchor_token: str) -> Optional[str]:
    """Map stem to Front/Back/Pocket/Sleeve when the marker follows anchor_token.

    The stem must start with anchor_token (case-insensitive). The side marker must be
    the first segment after that prefix: ``-f-`` / ``-b-`` / … or legacy ``-f`` / ``-b`` /
    … with nothing else before it. If anchor_token already ends with a legacy suffix
    (e.g. Step 4 token ``103671LG-f``), the matching label is returned even when the
    stem equals the token with no remainder.
    """
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
        if a.endswith(legacy) and (len(a) == len(legacy) or a[len(a) - len(legacy) - 1] == "-"):
            return label
    return None


def resolve_logo_anchor_for_slot(
    slot_index: int,
    row_series,
    *,
    fbpi_slots: List[Tuple[Path, str]],
    logo_design_tokens: Callable[..., List[str]],
) -> Optional[str]:
    """Logo/Design Image anchor for suffix detection on this logo slot.

  - **fbpi rows:** always the base token (first comma-separated value, side suffix
    stripped), so ``order-13-F-98765…`` matches base ``order-13``.
  - **Otherwise:** the token for that slot (e.g. ``103671LG-f`` from Step 4).
    """
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
) -> Optional[str]:
    """Front/Back/… label from fbpi slot pairing, if any."""
    if not fbpi_slots or slot_index < 1:
        return None
    fbpi_index = slot_index - 1
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
    return fbpi_side_label_for_slot(slot_index, fbpi_slots)


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


def resolve_position_tokens_for_row(
    row_series,
    position_code_to_draw: Optional[dict[str, str]],
    default_position_code: str,
    *,
    safe_str: Callable[[object], str],
    position_tokens: Callable[..., List[str]],
) -> List[str]:
    """Mirror banner position source from draw_page_banners_impl."""
    raw_position_val = safe_str(row_series.get("Position", ""))
    banner_source = raw_position_val
    if position_code_to_draw is not None and "/" not in raw_position_val:
        pos_code = safe_str(row_series.get("Position Code", ""))
        if pos_code == default_position_code:
            banner_source = ""
        elif pos_code:
            draw_val = safe_str(position_code_to_draw.get(pos_code, ""))
            if draw_val:
                banner_source = draw_val
    if not banner_source:
        return []
    return position_tokens(banner_source)


def slot_is_back_print(
    slot_index: int,
    img_path: Optional[Path],
    *,
    fbpi_slots: List[Tuple[Path, str]],
    row_series,
    position_code_to_draw: Optional[dict[str, str]],
    default_position_code: str,
    safe_str: Callable[[object], str],
    position_tokens: Callable[..., List[str]],
    logo_design_tokens: Callable[..., List[str]],
) -> bool:
    """True when a resolved logo cell should show the back-print grid hint."""
    if img_path is None:
        return False

    anchor = resolve_logo_anchor_for_slot(
        slot_index,
        row_series,
        fbpi_slots=fbpi_slots,
        logo_design_tokens=logo_design_tokens,
    )
    fbpi_label = fbpi_side_label_for_slot(slot_index, fbpi_slots)
    if logo_filename_indicates_back(img_path, anchor, fbpi_side_label=fbpi_label):
        return True

    raw_position_val = safe_str(row_series.get("Position", ""))
    if "/" not in raw_position_val:
        tokens = resolve_position_tokens_for_row(
            row_series,
            position_code_to_draw,
            default_position_code,
            safe_str=safe_str,
            position_tokens=position_tokens,
        )
        if slot_index < len(tokens):
            _has_front, _has_pocket, has_back = classify_position_token_impl(
                tokens[slot_index],
                safe_str=safe_str,
            )
            if has_back:
                return True

    return False


def next_logo_slot_index(slot_index: int) -> Optional[int]:
    """Logo slot index to the right in the same grid row, if any."""
    return {0: 1, 2: 3, 3: 4}.get(slot_index)
