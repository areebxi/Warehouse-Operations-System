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
    """`;` is OR. `+` inside one clause is AND (`Dancing Queen+Glitter`)."""
    return any(_name_clause(order, n) for n in _needles(spec))


def _name_clause(order: Order, clause: str) -> bool:
    parts = [p.strip() for p in clause.split("+") if p.strip()]
    return bool(parts) and all(_order_has_item_name_contains(order, p) for p in parts)

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

def _line_is_tee_category(ln: LineAttrs) -> bool:
    return _fold(ln.category) == "t-shirts"


def _line_is_hoodie_type(ln: LineAttrs) -> bool:
    return _fold(ln.product_type) in {"hoodie", "zip hoodie"}


def _line_is_sweatshirt_type(ln: LineAttrs) -> bool:
    return _fold(ln.product_type) == "sweatshirt"


def _line_is_odd_item(ln: LineAttrs) -> bool:
    """Printed remainder: not a tee, Gildan tee, babysuit, hoodie, or sweatshirt."""
    if _line_is_tee_category(ln) or _line_is_gildan_tee(ln):
        return False
    if _line_is_babysuit(ln) or _line_is_hoodie_type(ln) or _line_is_sweatshirt_type(ln):
        return False
    return True


def _order_gildan_any(order: Order) -> bool:
    """B40: every line is a t-shirt and any line is a Gildan tee."""
    lines = _chain_lines(order)
    return (
        bool(lines)
        and all(_line_is_tee_category(ln) for ln in lines)
        and any(_line_is_gildan_tee(ln) for ln in lines)
    )


def _order_tee_not_gildan(order: Order) -> bool:
    lines = _chain_lines(order)
    return (
        bool(lines)
        and all(_line_is_tee_category(ln) for ln in lines)
        and not any(_line_is_gildan_tee(ln) for ln in lines)
    )


def _order_resend_other(order: Order) -> bool:
    lines = _chain_lines(order)
    if not lines:
        return False
    return not any(
        _line_is_tee_category(ln) or _line_is_gildan_tee(ln) or _line_is_iron_on(ln) for ln in lines
    )


def _line_is_gildan_tee(ln: LineAttrs) -> bool:
    """B40: Brand Gildan, Gender Apparel contains GILDAN, or style 5000/G5000."""
    if _fold(ln.category) != "t-shirts":
        return False
    if _fold(ln.brand) == "gildan":
        return True
    if "gildan" in _fold(ln.gender_apparel):
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

# Needle "custom" also counts these whole words (locked 2026-10-14).
_CUSTOM_WORDS = re.compile(r"\b(?:custom|customisable|customised)\b")

def item_text_has_needle(text: str, needle: str) -> bool:
    """Substring match. Needle `custom` is a whole word, plus Customisable / Customised."""
    n = _norm_item_text(needle)
    hay = _norm_item_text(text)
    if not n:
        return False
    if n == "custom":
        return _CUSTOM_WORDS.search(hay) is not None
    return n in hay

def _order_has_item_name_contains(order: Order, needle: str) -> bool:
    if not _norm_item_text(needle):
        return False
    for ln in order.lines:
        if item_text_has_needle(ln.item_name, needle):
            return True
    for row in order.csv_rows:
        if item_text_has_needle(row.get("Item Name", ""), needle):
            return True
    return False
