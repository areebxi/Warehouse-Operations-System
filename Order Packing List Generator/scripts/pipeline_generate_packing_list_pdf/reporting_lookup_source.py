from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional


def _lookup_source_apparel(name: str, p: Optional[Path], stem_map: Optional[Dict[str, Path]]) -> str:
    """Explain how find_image resolved (or failed) for apparel."""
    if p is None:
        return "not_found"
    if stem_map:
        if stem_map.get(name) == p:
            return "indexed_stem_map_exact"
        lower = name.lower()
        for stem, path in stem_map.items():
            if stem.lower() == lower and path == p:
                return "indexed_stem_map_case_insensitive"
    return "filesystem_top_level_scan"

def _lookup_source_custom_logo(name: str, p: Optional[Path], stem_map: Optional[Dict[str, Path]]) -> str:
    if p is None:
        return "not_found"
    if stem_map:
        if stem_map.get(name) == p:
            return "indexed_stem_map_exact"
        lower = name.lower()
        for stem, path in stem_map.items():
            if stem.lower() == lower and path == p:
                return "indexed_stem_map_case_insensitive"
    return "filesystem_recursive_scan"

def _lookup_source_normal_logo(token: str, p: Optional[Path], stem_map: Optional[Dict[str, Path]]) -> str:
    if p is None:
        return "not_found"
    if stem_map:
        if stem_map.get(token) == p:
            return "indexed_stem_map_exact_token"
        for stem, path in stem_map.items():
            if path == p and stem.startswith(token):
                return f"indexed_stem_map_prefix_match (matched stem={stem!r})"
        token_lower = token.lower()
        for stem, path in stem_map.items():
            if path == p and stem.lower().startswith(token_lower):
                return f"indexed_stem_map_prefix_match_ci (matched stem={stem!r})"
    return "filesystem_prefix_scan"

def _custom_pdf_slot_token_label(
    slot: int,
    tokens: List[str],
    fbpi_slots: List[Tuple[Path, str]],
) -> str:
    """Human-readable token label for PDF customise slot trace (slot 0..4)."""
    if fbpi_slots:
        if slot == 0:
            return tokens[0] if tokens else "base"
        if 1 <= slot <= len(fbpi_slots):
            return f"{tokens[0]}-{fbpi_slots[slot - 1][1]} (fbpi)" if tokens else fbpi_slots[slot - 1][1]
        return f"slot {slot} (no fbpi pair)"
    if slot < len(tokens):
        return tokens[slot]
    return f"slot {slot}"

