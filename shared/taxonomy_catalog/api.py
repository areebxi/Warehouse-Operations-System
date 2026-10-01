"""Lookups and pick-list CSV row builder."""
from __future__ import annotations

from shared.taxonomy_catalog.aliases import ALIASES
from shared.taxonomy_catalog.code_maps import (
    BAG_TYPE_BY_CODE,
    HEAD_TYPE_BY_CODE,
    STYLE_BY_CODE,
)
from shared.taxonomy_catalog.dims import (
    CATEGORIES,
    DEFAULT_STYLE,
    DEPARTMENTS,
    PRODUCT_TYPES,
    SUBCATEGORIES,
)
from shared.taxonomy_catalog.duplicates import TYPE_DUPLICATE_STYLES
from shared.taxonomy_catalog.styles_list import PRODUCT_STYLES

# Add every supplier code as a style alias so a leftover code cell snaps to the name.
for _code, _name in STYLE_BY_CODE.items():
    ALIASES["product_style"].setdefault(_code, _name)
    ALIASES["product_style"].setdefault(_code.lower(), _name)


def style_from_code(token: object) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    return STYLE_BY_CODE.get(raw.upper(), "")


def bag_type_from_code(token: object) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    return BAG_TYPE_BY_CODE.get(raw.upper(), "")


def head_type_from_code(token: object) -> str:
    raw = str(token or "").strip()
    if not raw:
        return ""
    return HEAD_TYPE_BY_CODE.get(raw.upper(), "")


def collapse_style(style: str) -> str:
    s = (style or "").strip()
    if not s:
        return ""
    if s.casefold() in {x.casefold() for x in TYPE_DUPLICATE_STYLES}:
        return DEFAULT_STYLE
    return s


def csv_rows() -> list[tuple[str, str, str, str]]:
    """dimension, value, maps_to, source — canonical first, then aliases."""
    blocks: list[tuple[str, tuple[str, ...]]] = [
        ("category", CATEGORIES),
        ("subcategory", SUBCATEGORIES),
        ("product_type", PRODUCT_TYPES),
        ("product_style", PRODUCT_STYLES),
        ("department", DEPARTMENTS),
    ]
    rows: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for dim, values in blocks:
        folded = [s.casefold() for s in values]
        if len(folded) != len(set(folded)):
            raise ValueError(f"duplicate {dim} values")
        for value in values:
            key = (dim, value.casefold())
            if key in seen:
                continue
            seen.add(key)
            rows.append((dim, value, "", "warehouse"))
        for alias, canonical in sorted(ALIASES.get(dim, {}).items(), key=lambda kv: kv[0].casefold()):
            if alias.casefold() == canonical.casefold():
                continue
            if canonical not in values and canonical.casefold() not in folded:
                raise ValueError(f"{dim} alias {alias!r} maps to unknown {canonical!r}")
            key = (dim, alias.casefold())
            if key in seen:
                continue
            seen.add(key)
            rows.append((dim, alias, canonical, "alias"))
    return rows
