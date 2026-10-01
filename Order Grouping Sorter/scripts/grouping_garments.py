"""Garment / SKU predicates for fixed-batch matching."""
from __future__ import annotations

import re

from shared.areeb_taxonomy import cell

from grouping_intake import _has_tag
from grouping_models import IN_HOUSE, RESEND_TAG, LineAttrs, Order, _fold
from grouping_slots import _chain_lines

def _sku_parts(sku: str) -> set[str]:
    return {p.strip().casefold() for p in (sku or "").split("-")}

def _needles(spec: str) -> list[str]:
    return [n.strip() for n in spec.split(";") if n.strip()]

def _sku_hit(sku: str, needle: str) -> bool:
    """`=M61` = whole dash-separated SKU part; else case-insensitive substring."""
    if needle.startswith("="):
        return needle[1:].casefold() in _sku_parts(sku)
    return needle.casefold() in _fold(sku)

def _order_sku_any(order: Order, spec: str) -> bool:
    needles = _needles(spec)
    return any(_sku_hit(ln.sku, n) for ln in order.lines for n in needles)

def _order_name_any(order: Order, spec: str) -> bool:
    return any(_order_has_item_name_contains(order, n) for n in _needles(spec))

def _destination_slot(order: Order) -> str:
    """Blank country is not guessed international."""
    c = cell(order.ship_country).upper()
    return "international" if c and c != "GB" else "uk"

BABYSUIT_STYLES = frozenset({"c800t", "c8020t", "c8030t"})

def _line_is_mug(ln: LineAttrs) -> bool:
    return (
        "mug" in _fold(ln.sku)
        or "m61" in _sku_parts(ln.sku)
        or _fold(ln.printing_type) == "sublimation"
    )

def _line_is_babysuit(ln: LineAttrs) -> bool:
    return bool(BABYSUIT_STYLES & _sku_parts(ln.sku)) or _fold(ln.product_type) == "body suit"

def _line_is_ss_fotl(ln: LineAttrs) -> bool:
    # Garment + FOTL brand. Warehouse Stock vs On Demand is the CSV supply-method
    # cell (B100 vs B50). Locked 2026-09-30.
    brand = _fold(ln.brand)
    if "fruit of the loom" not in brand and brand != "fotl":
        return False
    if _fold(ln.category) != "t-shirts":
        return False
    pt = _fold(ln.product_type)
    if not pt:
        return False
    if "long sleeve" in pt or "longsleeve" in pt:
        return False
    return "short sleeve" in pt or "t-shirt" in pt

def _line_is_iron_on(ln: LineAttrs) -> bool:
    """Catalog iron-on OR Item SKU contains IronOn (supervisor 2026-09-28). Never sticker."""
    cat = _fold(ln.category)
    pt = _fold(ln.product_type)
    if "sticker" in cat or "sticker" in pt or "sticker" in _fold(ln.sku):
        return False
    if "ironon" in _fold(ln.sku):
        return True
    if _fold(ln.supply_method) != _fold(IN_HOUSE):
        return False
    return cat == "iron-on" or "iron-on" in pt or "iron on" in pt

def _has_gildan_5000_token(text: str) -> bool:
    """Style 5000 / G5000 as a token — not substring of 15000 (FOTL UID false hit)."""
    for part in re.split(r"[^A-Za-z0-9]+", text or ""):
        p = part.casefold()
        if p in {"5000", "g5000"}:
            return True
    return False

def _line_is_gildan_tee(ln: LineAttrs) -> bool:
    """B40: Brand Gildan T-Shirts, or style 5000/G5000 in SKU / Gender Apparel."""
    if _fold(ln.category) != "t-shirts":
        return False
    if _fold(ln.brand) == "gildan":
        return True
    return _has_gildan_5000_token(ln.sku) or _has_gildan_5000_token(ln.gender_apparel)

def _all_chain(order: Order, pred) -> bool:
    lines = _chain_lines(order)
    return bool(lines) and all(pred(ln) for ln in lines)

def _order_status_slot(order: Order) -> str:
    """Graph order-status: resend tag wins; else awaiting_shipment (pool)."""
    if _has_tag(order.tag_names, RESEND_TAG):
        return "resend"
    return "awaiting_shipment"

def _norm_item_text(s: str) -> str:
    """Casefold; treat hyphens as spaces so Glow-in-the-Dark ≈ Glow In The Dark."""
    return " ".join(_fold(s).replace("-", " ").split())

def _order_has_item_name_contains(order: Order, needle: str) -> bool:
    n = _norm_item_text(needle)
    if not n:
        return False
    for ln in order.lines:
        if n in _norm_item_text(ln.item_name):
            return True
    for row in order.csv_rows:
        if n in _norm_item_text(row.get("Item Name", "")):
            return True
    return False
