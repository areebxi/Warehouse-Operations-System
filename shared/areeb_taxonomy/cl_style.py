"""Style helpers for CL Gender Apparel classify."""
from __future__ import annotations

import re

import shared.taxonomy_catalog as tax
from shared.areeb_taxonomy.consts import (
    _CL_BRAND_PREFIXES,
    _HIVIS_RE,
    _KIDS_RE,
    _MENS_RE,
    _UNISEX_RE,
    _WOMENS_RE,
)
from shared.areeb_taxonomy.garment_tables import _GARMENT_PHRASES, _IRON_SIZES, _KIND_STYLE
from shared.areeb_taxonomy.values import _fold_ga, _norm_ga

# Late import avoids cycle with cl_type (_codes_in lives there).


def _codes_in_for_style(text: str) -> list[str]:
    from shared.areeb_taxonomy.cl_type import _codes_in

    return _codes_in(text)


def _ironon_style(ga: str) -> str:
    lower = ga.casefold()
    for prefix in ("dtf-ironon-", "dtf-ironon", "ironon-", "ironon"):
        if lower.startswith(prefix):
            rest = ga[len(prefix) :].lstrip("-")
            return rest or "Iron-On"
    return "Iron-On"


def _strip_brand(folded: str) -> str:
    for prefix in _CL_BRAND_PREFIXES:
        if folded == prefix:
            return ""
        if folded.startswith(prefix + " ") or folded.startswith(prefix + "-"):
            return folded[len(prefix) :].lstrip(" -")
    return folded


def _title_style(text: str) -> str:
    bits: list[str] = []
    for raw in text.replace("-", " ").split():
        low = raw.casefold()
        if low in {"ux", "v"}:
            bits.append(raw.upper())
        elif low in {"hi-viz", "hi-vis", "hiviz", "hivis"}:
            bits.append("Hi-Vis")
        elif low in {"t", "shirt"} and bits and bits[-1] == "T":
            bits[-1] = "T-Shirt"
        else:
            bits.append(raw[:1].upper() + raw[1:].lower() if raw else raw)
    return " ".join(bits)


def _style_from_ga(ga: str, kind: str) -> str:
    orig = _norm_ga(ga)
    cf = _fold_ga(ga)
    if cf.startswith("dtf-ironon") or cf.startswith("ironon"):
        rest = _ironon_style(orig)
        if rest.upper() in _IRON_SIZES:
            return rest.upper()
        named = tax.style_from_code(rest) or tax.style_from_code(rest.replace("-", ""))
        if named:
            return named
        for token in _codes_in_for_style(rest):
            hit = tax.style_from_code(token)
            if hit:
                return hit
        if rest.casefold() in {"k-t", "kt"}:
            return "Kids T-Shirt"
        return tax.collapse_style(_title_style(rest) or tax.DEFAULT_STYLE)
    for token in _codes_in_for_style(orig):
        hit = tax.style_from_code(token)
        if hit:
            return hit
    for needle, canon in tax.STYLE_PHRASES:
        if needle in cf:
            return canon
    folded = _strip_brand(cf)
    folded = _KIDS_RE.sub(" ", folded)
    folded = _WOMENS_RE.sub(" ", folded)
    folded = _MENS_RE.sub(" ", folded)
    folded = _UNISEX_RE.sub(" ", folded)
    folded = _HIVIS_RE.sub(" ", folded)
    for phrase in _GARMENT_PHRASES:
        folded = folded.replace(phrase, " ")
    folded = re.sub(r"\s+", " ", folded).strip(" -")
    if folded.endswith(" t"):
        folded = folded[:-2].strip()
    leftover_map = {
        "heavy": "Heavy Cotton",
        "china": "China Bag",
    }
    if folded in leftover_map:
        return leftover_map[folded]
    if folded:
        titled = _title_style(folded)
        return tax.collapse_style(titled)
    return tax.collapse_style(_KIND_STYLE.get(kind, tax.DEFAULT_STYLE))
