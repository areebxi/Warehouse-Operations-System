"""Prefix-skip helpers so LOCATION / F/B/P/S stems are not stolen as base logos."""

from __future__ import annotations

from pipeline_generate_packing_list_pdf.back_print_hint import FBPI_SIDE_SUFFIX_LOOKUP


def fbpi_stem_matches_token(stem: str, base_token: str) -> bool:
    """True when stem is exactly base_token, or base_token plus a hyphenated remainder."""
    if not stem or not base_token:
        return False
    sl = stem.lower()
    bl = base_token.lower()
    return sl == bl or sl.startswith(bl + "-")


def stem_is_location_for_token(stem: str, token: str) -> bool:
    """True when stem is ``{token}-LOCATION`` or ``{token}-LOCATION-...``."""
    if not stem or not token:
        return False
    return fbpi_stem_matches_token(stem, f"{token}-LOCATION")


def stem_is_fbpi_side_for_token(stem: str, token: str) -> bool:
    """True when stem is a Front/Back/Pocket/Sleeve (incl. S1/S2/SL/SR) file for token."""
    if not stem or not token:
        return False
    return any(
        fbpi_stem_matches_token(stem, f"{token}-{suffix}")
        for suffix, _label in FBPI_SIDE_SUFFIX_LOOKUP
    )


def skip_custom_logo_prefix_stem(stem: str, token: str) -> bool:
    """Prefix lookup must not steal LOCATION or F/B/P/S side files as the base design."""
    return stem_is_location_for_token(stem, token) or stem_is_fbpi_side_for_token(stem, token)
