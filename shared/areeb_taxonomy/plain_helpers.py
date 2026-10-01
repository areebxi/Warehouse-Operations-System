"""Plain gender / pick helpers for leftover Description mapping."""
from __future__ import annotations

from shared.areeb_taxonomy.consts import (
    GENDER_KIDS,
    GENDER_MENS,
    GENDER_UNISEX,
    GENDER_WOMENS,
    _PLAIN_KIDS_RE,
    _PLAIN_WOMENS_RE,
    _UNISEX_RE,
)


def _plain_gender(desc: str) -> str:
    if _PLAIN_KIDS_RE.search(desc):
        return GENDER_KIDS
    if _PLAIN_WOMENS_RE.search(desc):
        return GENDER_WOMENS
    if _UNISEX_RE.search(desc):
        return GENDER_UNISEX
    return GENDER_MENS


def _plain_pick(g: str, mens: str, ladies: str, kids: str, unisex: str | None = None) -> str:
    if g == GENDER_KIDS:
        return kids
    if g == GENDER_WOMENS:
        return ladies
    if g == GENDER_UNISEX:
        return unisex or mens
    return mens
