"""Token rules for 1-SP JPEG position hints (no I/O).

A dedicated hyphen segment before the full SKU (`-P-`, `-S-`, `-S1-`, `-S2-`,
`-SL-`, `-SR-`) marks a companion JPEG. Apparel size `S` inside the SKU is not
a token.
"""

from typing import Optional, Tuple

# Longer sleeve tokens before plain S so S1/SL are not missed.
POSITION_HINT_TOKENS = ("S1", "S2", "SL", "SR", "P", "S")
POSITION_HINT_EXTENSIONS = (".jpg", ".jpeg")
POSITION_HINT_MM = {
    "P": (80.0, 100.0),
    "S": (100.0, 100.0),
    "S1": (100.0, 100.0),
    "S2": (100.0, 100.0),
    "SL": (100.0, 100.0),
    "SR": (100.0, 100.0),
}
_SLEEVE_TOKENS = frozenset({"S", "S1", "S2", "SL", "SR"})


def normalize_position_token(token: Optional[str]) -> Optional[str]:
    if token is None:
        return None
    t = str(token).strip().upper()
    if t in POSITION_HINT_MM:
        return t
    return None


def flags_for_position_token(token: Optional[str]) -> Tuple[Optional[str], bool, bool]:
    """Return (token, is_pocket, is_sleeve). Unknown token → (None, False, False)."""
    t = normalize_position_token(token)
    if t is None:
        return None, False, False
    if t == "P":
        return t, True, False
    if t in _SLEEVE_TOKENS:
        return t, False, True
    return None, False, False


def target_mm_for_position_token(token: Optional[str]) -> Optional[Tuple[float, float]]:
    t = normalize_position_token(token)
    if t is None:
        return None
    return POSITION_HINT_MM[t]
