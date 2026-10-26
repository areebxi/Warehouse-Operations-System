"""Exact `{designCode}-{index}.png` files (Front/Back/Pocket/Sleeve).

Letter indexes are separate designs. Do not treat them as a prefix of the base code.
"""

from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

# Longer sleeve tokens before plain S. Same order as packing FBPI slots. Cap 4.
_INDEX_SUFFIXES = ("f", "b", "p", "s1", "s2", "sl", "sr", "s")
# CL position names that print from a letter-index PNG (5968ALG-P.png / -B.png).
_NAME_TO_INDEX = {
    "front center": "F",
    "back center": "B",
    "front left pocket": "P",
    "front right pocket": "P",
    "pocket": "P",
    "left sleeve": "SL",
    "right sleeve": "SR",
    "sleeve": "S",
}
_MAX_INDEXES = 4
# ponytail: one listing per folder for this process. Files added later are missed until restart.
_NAME_CACHE: dict = {}


def _names_by_lower(folder: str) -> dict:
    cached = _NAME_CACHE.get(folder)
    if cached is not None:
        return cached
    names = {}
    for name in os.listdir(folder):
        names.setdefault(name.lower(), name)
    _NAME_CACHE[folder] = names
    return names


def index_letter_for_position(position: Optional[str]) -> Optional[str]:
    """Map a Custom Label position name to its letter-index file suffix."""
    if not position:
        return None
    return _NAME_TO_INDEX.get(str(position).strip().casefold())


def find_design_index_pngs(
    stems: Sequence[str],
    folder: Optional[str],
) -> List[Tuple[str, str]]:
    """Return (path, suffix) for exact index PNGs. Suffix is upper-case."""
    if not folder or not os.path.isdir(folder):
        return []
    on_disk = _names_by_lower(folder)
    found: List[Tuple[str, str]] = []
    seen_stems = set()
    for stem in stems:
        key = str(stem or "").strip()
        if not key or key.lower() in seen_stems:
            continue
        seen_stems.add(key.lower())
        for suffix in _INDEX_SUFFIXES:
            if len(found) >= _MAX_INDEXES:
                return found
            real_name = on_disk.get(f"{key}-{suffix}.png".lower())
            if not real_name:
                continue
            found.append((os.path.join(folder, real_name), suffix.upper()))
    return found
