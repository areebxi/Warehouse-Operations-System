"""Label parse helpers / regexes / constants for add_labels."""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_WAREHOUSE = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(_WAREHOUSE))

from shared.cl_sku_match import key_after_first_dash  # noqa: E402
from fill_from_seeds import clean  # noqa: E402

SEED_COLS = (
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
    "Customise",
)

RE_MOCK_P_UID = re.compile(r"^(M\d+)(?:-P\d+)?-(\d+)$", re.I)
RE_MOCK_TOKEN = re.compile(r"^(M\d+)(?:-P\d+)?-", re.I)
RE_C800T_AGE = re.compile(
    # Optional -P# — listing SKUs sometimes omit it (M281-C800T-30-3>6).
    # ShipStation / HTML sometimes encodes > as &gt;.
    r"^(M\d+(?:-P\d+)?-C800T-\d+-)(\d+(?:>|&gt;)\d+|\d+-\d+)$",
    re.I,
)
# A515-PHOTO = A5 15mm. A410 in P5-ACPPLQ-A410-PB = A4 10mm. A625 = A6 25mm. A715 = A7 15mm.
RE_ACRYLIC_SIZE = re.compile(r"(?:^|-)A([4-7])(\d{2})(?:-|$)", re.I)
_ACRYLIC_PAPER = {
    "4": ("A4", "210", "297"),
    "5": ("A5", "148", "210"),
    "6": ("A6", "105", "148"),
    "7": ("A7", "74", "105"),
}
# Amazon hoodie size codes: ARM-BBe-C1-D6-EF / AS3-BCA-C1-D6-EF (D6-EF = Large).
RE_AMZ_SIZE_CODE = re.compile(
    r"^([A-Za-z]{2,3}-[A-Za-z0-9]+)-([A-Za-z0-9]+)-(D\d+)-(E[A-Za-z0-9]+)$",
    re.I,
)
RE_BAG_COLOUR = re.compile(r"^(W\d+|BG-W\d+|BG-[A-Z0-9]+)-([A-Za-z0-9]+)-O/S", re.I)
# Optional DTF- prefix: M280-P5-IronOn-A6 and M280-P5-DTF-IronOn-A6.
RE_IRONON = re.compile(r"(?:DTF-)?IronOn-A(\d+)", re.I)
_IRONON_PAPER = {"4": ("210", "297"), "5": ("148", "210"), "6": ("105", "148")}
RE_STICKER = re.compile(r"(?:STICKERS?|STCKR)-([A-Z])\s*\(([^)]+)\)", re.I)
# Packing SKU DTF-Transfer-1M-1 → Custom Label Transfer-1M-1 (after first dash).
RE_TRANSFER = re.compile(r"^Transfer-(\d+M)(?:-\d+)?$", re.I)
# Warehouse garment: W-H-BLK-M / M-T-BLK-M / K-H-DHR-YXS (gender-type-colour-size).
RE_WAREHOUSE_GARMENT = re.compile(
    r"^(M|W|K)-(T|H|SS|SW|PS)-([A-Za-z0-9]+)-"
    r"(Y(?:2XL|XS|XL|S|M|L)|(?:[2-5]XL|XXL|XS|XL|S|M|L))$",
    re.I,
)
# Gildan Heavy Cotton style code in the packing SKU after first dash: 5000-NAT-S
_SIZE_TOKEN = r"(Y(?:2XL|XS|XL|S|M|L)|(?:[2-5]XL|XXL|XS|XL|S|M|L))"
RE_GILDAN_5000 = re.compile(rf"^5000-([A-Za-z0-9]+)-{_SIZE_TOKEN}$", re.I)
# W415-NAT-L-Yes / BG-W530-NAT-L-Yes (letter size, not O/S).
RE_BAG_SIZE_YES = re.compile(
    rf"^(W\d+|BG-W\d+)-([A-Za-z0-9]+)-{_SIZE_TOKEN}-Yes$",
    re.I,
)
_BAG_SIZE_NAME = {
    "xxs": "Extra Extra Small",
    "xs": "Extra Small",
    "s": "Small",
    "m": "Medium",
    "l": "Large",
    "xl": "Extra Large",
    "2xl": "2XL",
    "3xl": "3XL",
    "yxs": "YXS",
    "ys": "YS",
    "ym": "YM",
    "yl": "YL",
    "yxl": "YXL",
    "y2xl": "Y2XL",
}
_WAREHOUSE_GA = {
    ("M", "T"): "Mens-T-Shirt",
    ("W", "T"): "Womens-T-Shirt",
    ("K", "T"): "Kids-T-Shirt",
    ("M", "H"): "Mens-Hoodie",
    ("W", "H"): "Womens-Hoodie",
    ("K", "H"): "Kids-Hoodie",
    ("M", "SW"): "Mens-Sweatshirt",
    ("W", "SW"): "Womens-Sweatshirt",
    ("K", "SW"): "Kids-Sweatshirt",
}
_WAREHOUSE_COLOUR = {
    "blk": "Black",
    "whi": "White",
}

# Abbrev colour codes seen on bag Custom Labels → Colour name
_BAG_COLOUR = {
    "skybe": "Sky Blue",
    "clard": "Classic Red",
    "clardow": "Classic Red-Off White",
    "frenyow": "French Navy-Off White",
    "blabk": "Black-Black",
    "limgn": "Lime",
    "dusbe": "Dusty Blue",
    "nat": "Natural",
    "blk": "Black",
    "nvy": "Navy",
    "red": "Red",
    "bur": "Burgundy",
    "cpnk": "Classic Pink",
}

# Supervisor 15 Sep 2026: packing shirt colour tokens that are not the CL code.
# Peer lookup only — Custom Label keeps NAV / PUE.
_SHIRT_COLOUR_ALIAS = {
    "nav": "nvy",  # Navy
    "pue": "prp",  # Purple
}


def label_from_input(raw: str, *, from_sku: bool) -> str:
    s = clean(raw)
    if not s:
        return ""
    if from_sku:
        after = key_after_first_dash(s)
        return after or s
    # packing SKU pasted without flag: has design prefix then mock/bag tail
    if re.match(r"^\d+[A-Za-z]*-", s) and key_after_first_dash(s):
        return key_after_first_dash(s)
    return s


def _age_to_size(token: str) -> str:
    t = token.replace("&gt;", "-").replace(">", "-")
    if re.fullmatch(r"\d+-\d+", t):
        return f"{t} Months"
    return t


def _sticker_size(inner: str) -> str:
    compact = re.sub(r"\s+", "", clean(inner))
    return re.sub(r"[x×]", " x ", compact, count=1, flags=re.I)


def _sticker_mm(inner: str) -> tuple[str, str] | None:
    """50cmx50cm → ('500', '500'). Token drives mm; peer mm may be blank/wrong letter."""
    nums = re.findall(r"(\d+)\s*cm", clean(inner), flags=re.I)
    if len(nums) >= 2:
        return str(int(nums[0]) * 10), str(int(nums[1]) * 10)
    if len(nums) == 1:
        mm = str(int(nums[0]) * 10)
        return mm, mm
    return None


def _bag_ga(prod: str, peer: dict[str, str] | None) -> str:
    ga = clean(peer.get("Gender Apparel")) if peer else ""
    if ga.startswith("BG-"):
        return ga
    if prod.upper().startswith("BG-"):
        return prod.upper()
    if prod.upper().startswith("W"):
        return f"BG-{prod.upper()}"
    return ga or prod
