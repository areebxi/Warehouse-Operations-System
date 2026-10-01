"""Supply Method for grouping.

Supervisor lock 2026-09-09, tightened for Custom Label on 2026-09-23:
  Warehouse Stock        = CL: FOTL men / women / kids t-shirts in the locked
                           colour lists, plus Kids body styles C800T / C8030T
                           in the locked body colours.
                           Plain / Packs: all FOTL men / women / kids t-shirts
                           (no colour list).
  In House Manufacture   = Custom Label SKU or Gender Apparel contains
                           iron on / ironon / iron-on / sticker
                           (CL / printed only; plain cannot be in-house)
  Supplier On Demand     = everything else (off-list FOTL colours, Gildan, …)

Do not reuse CL column `Warehouse Stock` (Yes on China bags — not this split).
Colour match is the whole Colour cell, casefold only. Deep Navy is not Navy.
"""
from __future__ import annotations
import re
from typing import Any
from shared.areeb_taxonomy import cell
WAREHOUSE_GA_TEES = frozenset({"Mens-T-Shirt", "Womens-T-Shirt", "Kids-T-Shirt"})
_MENS_TEE_COLOURS = (
    "Azure Blue", "Black", "Bottle Green", "Burgundy", "Charcoal", "Classic Olive",
    "Daisy", "Dark Heather Grey", "Forest Green", "Fuchsia", "Heather Grey",
    "Irish Green", "Kelly Green", "Light Blue", "Light Graphite", "Light Graphite Grey",
    "Light Pink", "Maroon", "Military Green", "Natural", "Navy", "Navy Blue",
    "Orange", "Purple", "Red", "Royal", "Royal Blue", "Sapphire", "Sky Blue",
    "Sports Grey", "Sunflower", "White", "Yellow",
)
_WOMENS_TEE_COLOURS = (
    "Black", "Burgundy", "Charcoal", "Classic Olive", "Daisy", "Dark Heather Grey",
    "Fuchsia", "Heather Grey", "Heliconia", "Irish Green", "Kelly Green", "Light Blue",
    "Light Graphite", "Light Graphite Grey", "Light Pink", "Maroon", "Military Green",
    "Natural", "Navy", "Navy Blue", "Orange", "Purple", "Red", "Royal", "Royal Blue",
    "Sky Blue", "Sunflower", "White",
)
_KIDS_TEE_COLOURS = (
    "Azure Blue", "Black", "Burgundy", "Charcoal", "Daisy", "Fuchsia", "Heather Grey",
    "Heliconia", "Irish Green", "Kelly Green", "Light Blue", "Light Graphite",
    "Light Graphite Grey", "Light Pink", "Maroon", "Natural", "Navy", "Navy Blue",
    "Orange", "Purple", "Red", "Royal", "Royal Blue", "Sapphire", "Sky Blue",
    "Sports Grey", "Sunflower", "White",
)
_BODY_COLOURS = (
    "Black", "Lemon Yellow", "Light Blue", "Light Pink", "Red", "Sports Grey", "White",
)
def _fold_set(names: tuple[str, ...]) -> frozenset[str]:
    return frozenset(n.casefold() for n in names)
WAREHOUSE_TEE_COLOURS = {
    "mens": _fold_set(_MENS_TEE_COLOURS),
    "womens": _fold_set(_WOMENS_TEE_COLOURS),
    "kids": _fold_set(_KIDS_TEE_COLOURS),
}
WAREHOUSE_BODY_COLOURS = _fold_set(_BODY_COLOURS)
_DEPT_KEY = {
    "mens": "mens",
    "men": "mens",
    "womens": "womens",
    "women": "womens",
    "ladies": "womens",
    "lady": "womens",
    "kids": "kids",
    "kid": "kids",
}
_VEST_RE = re.compile(r"\b(?:vests?|tanks?|camisoles?)\b", re.I)
_BODY_STYLE_RE = re.compile(r"\b(?:C800T|C8030T)\b", re.I)
def _fold(value: object) -> str:
    return cell(value).casefold()
def _compact(value: object) -> str:
    return "".join(ch for ch in _fold(value) if ch.isalnum())
def is_gildan_brand(brand: object) -> bool:
    return "gildan" in _fold(brand)
def is_fotl_brand(brand: object) -> bool:
    folded = _fold(brand)
    if not folded:
        return False
    if "fruit" in folded and "loom" in folded:
        return True
    compact = _compact(brand)
    return compact in {"fotl", "folt"} or compact.startswith("fotl") or compact.startswith("folt")
def is_in_house_text(*parts: object) -> bool:
    """SKU / Gender Apparel contains iron on, ironon, iron-on, or sticker."""
    blob = "".join(_compact(p) for p in parts)
    return "ironon" in blob or "sticker" in blob
def is_vest_or_tank(
    *,
    product_type: object = "",
    gender_apparel: object = "",
    description: object = "",
) -> bool:
    blob = " ".join((_fold(product_type), _fold(gender_apparel), _fold(description)))
    return bool(_VEST_RE.search(blob))
def is_tshirt(
    *,
    category_areeb: object = "",
    product_type: object = "",
    gender_apparel: object = "",
    description: object = "",
) -> bool:
    if cell(category_areeb).upper() != "T-SHIRTS":
        return False
    return not is_vest_or_tank(
        product_type=product_type,
        gender_apparel=gender_apparel,
        description=description,
    )
def is_fotl(
    *,
    brand: object = "",
    gender_apparel: object = "",
) -> bool:
    """Fruit of the Loom identity. Gildan brand always wins (on-demand)."""
    if is_gildan_brand(brand):
        return False
    if is_fotl_brand(brand):
        return True
    ga = cell(gender_apparel)
    ga_fold = ga.casefold()
    if (
        ga_fold.startswith("fotl")
        or ga_fold.startswith("folt")
        or ga_fold.startswith("fruit of the loom")
    ):
        return True
    if ga in WAREHOUSE_GA_TEES:
        return not cell(brand) or is_fotl_brand(brand)
    return False
def is_cl_warehouse_tee_colour(department: object, colour: object) -> bool:
    """True when this department's locked FOTL tee colour list contains Colour."""
    key = _DEPT_KEY.get(_fold(department))
    if not key:
        return False
    return _fold(colour) in WAREHOUSE_TEE_COLOURS[key]
def is_cl_warehouse_body_suit(
    *,
    department: object = "",
    colour: object = "",
    custom_label: object = "",
    gender_apparel: object = "",
    product_code: object = "",
) -> bool:
    """Kids C800T / C8030T in the locked body colours. C8020T is not stock."""
    if _DEPT_KEY.get(_fold(department)) != "kids":
        return False
    if _fold(colour) not in WAREHOUSE_BODY_COLOURS:
        return False
    blob = " ".join(cell(p) for p in (custom_label, gender_apparel, product_code))
    return bool(_BODY_STYLE_RE.search(blob))
