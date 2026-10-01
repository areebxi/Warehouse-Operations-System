"""BTC Stock ID size/colour map tables and size mapping."""

from __future__ import annotations

# Custom Label full name -> BTC Product Data abbreviation
SIZE_TO_PRODUCT_EXPORT: dict[str, str] = {
    "small": "S",
    "medium": "M",
    "large": "L",
    "extra large": "XL",
    "extra-large": "XL",
    "x-large": "XL",
    "x large": "XL",
    "xs": "XS",
    "2xl": "2XL",
    "3xl": "3XL",
    "4xl": "4XL",
    "5xl": "5XL",
    "one size": "O/S",
    "o/s": "O/S",
    "standard size": "O/S",
}

# Youth SPCs: Custom Label age label -> BTC Product Data letter size (18000B, 18500B, SF500B)
YOUTH_LETTER_SPCS = frozenset(x.casefold() for x in ("18000B", "18500B", "SF500B"))
YOUTH_AGE_TO_LETTER_SIZE: dict[str, str] = {
    "3-4 years": "XS",
    "4 years": "XS",
    "4-5 years": "XS",
    "5-6 years": "S",
    "5 years": "S",
    "7-8 years": "S",
    "9-11 years": "M",
    "12-14 years": "L",
    "12-13 years": "L",
    "14-15 years": "XL",
    "1-2 years": "XS",
    "2 years": "XS",
    "2-3 years": "XS",
    "3 years": "XS",
    "0-3 months": "XS",
    "3-6 months": "XS",
    "6-12 months": "XS",
    "12-18 months": "XS",
    "18-24 months": "XS",
}

# Baby/toddler SPCs: age label -> BTC Product Data month/year code (BZ02, BZ10)
BZ_MONTH_SPCS = frozenset(x.casefold() for x in ("BZ02", "BZ10"))
BZ_AGE_TO_MONTH_CODE: dict[str, str] = {
    "0-3 months": "0-3",
    "3-6 months": "3-6",
    "6-12 months": "6-12",
    "12-18 months": "12-18",
    "18-24 months": "18-24",
    "2-3 years": "2-3",
}

# Custom Label colour name -> BTC Product Data Colour Name (lookup only; CSV unchanged)
COLOUR_ALIASES: dict[str, str] = {
    "navy": "Navy Blue",
    "royal blue": "Royal",
    "dark royal": "Royal",
    "sports grey": "Sport Grey",
    "dark heather grey": "Dark Heather",
    "classic pink": "Classic Pink/ Light Grey",
    "fuchsia": "Fuchsia/Graphite",
    "lime": "Lime/graphite",
    "purple": "Purple/Light Grey",
    "classic pink-graphite": "Graphite",
    "fuchsia-graphite": "Graphite",
    "light purple": "Purple",
    "yellow": "Yellow/Graphite Grey",
    "surf blue": "Surf Blue/ Graphite Grey",
    "surf blue-graphite grey": "Graphite",
    "natural-black": "Natural",
    "natural-fuchsia": "Natural",
    "natural-lime": "Natural",
    "antique cherry red": "Red",
    "black-black": "Black",
    "sky blue-french navy": "French Navy",
    "orange": "Orange/Graphite Grey",
    "emerald-graphite": "Graphite",
}


def norm(value: str) -> str:
    return (value or "").strip().casefold()


def cl_size_to_pe(size: str, spc: str = "") -> tuple[str, bool]:
    """Map Custom Label size to BTC Product Data size. Returns (pe_size, used_kids_map)."""
    key = norm(size)
    ns = norm(spc)

    adult = SIZE_TO_PRODUCT_EXPORT.get(key)
    if adult:
        return adult, False

    if ns in BZ_MONTH_SPCS:
        bz_mapped = BZ_AGE_TO_MONTH_CODE.get(key)
        if bz_mapped:
            return bz_mapped, True

    if ns in YOUTH_LETTER_SPCS:
        youth_mapped = YOUTH_AGE_TO_LETTER_SIZE.get(key)
        if youth_mapped:
            return youth_mapped, True

    return (size or "").strip(), False


def colours_to_try(colour_name: str) -> list[str]:
    """Normalized colour keys to try: original first, then alias."""
    raw = (colour_name or "").strip()
    if not raw:
        return []

    keys = [norm(raw)]
    alias = COLOUR_ALIASES.get(norm(raw))
    if alias:
        alias_key = norm(alias)
        if alias_key not in keys:
            keys.append(alias_key)
    return keys
