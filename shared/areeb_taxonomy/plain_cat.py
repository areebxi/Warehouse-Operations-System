"""Plain Description → BTC Department / Sub Department mapping."""
from __future__ import annotations

import re

from shared.areeb_taxonomy.consts import GENDER_KIDS, _HIVIS_RE
from shared.areeb_taxonomy.plain_helpers import _plain_gender, _plain_pick
from shared.areeb_taxonomy.values import _fold_ga

def _plain_cat_type(desc: str) -> tuple[str, str]:
    """Map Plain Description → BTC Department / Sub Department. Empty desc → blank."""
    cf = _fold_ga(desc)
    if not cf:
        return "", ""
    g = _plain_gender(desc)
    if _HIVIS_RE.search(cf):
        ptype = "Childrens Hi-Vis" if g == GENDER_KIDS else "Hi Vis Clothing"
        return "Safetywear", ptype
    if any(tok in cf for tok in ("backpack", "tote", "shopper", "holdall", "duffle", "duffel", "rucksack")):
        return "Bags", "Bags, Backpacks Etc"
    if re.search(r"\bbag\b", cf) and "bodybag" not in cf:
        return "Bags", "Bags, Backpacks Etc"
    if any(tok in cf for tok in ("scarf", "neckwarmer", "snood")):
        return "HEADWEAR", "Scarves And Neckwear"
    if any(tok in cf for tok in ("beanie", "snapback", "trucker", "dad cap")) or re.search(
        r"\b(cap|hat|hats)\b", cf
    ):
        return "HEADWEAR", "Caps & Hats Etc"
    if "hoodie" in cf or "hooded" in cf or re.search(r"\bhoody\b", cf):
        return "SWEATSHIRTS AND HOODIES", _plain_pick(
            g,
            "Mens Sweatshirts & Hoodies",
            "Ladies Sweatshirts And Hoodies",
            "Childrens Sweatshirts And Hoodies",
            "UNISEX SWEATSHIRTS & HOODIES",
        )
    if "sweatshirt" in cf or "crewneck" in cf or "crew neck" in cf or re.search(r"\bsweat\b", cf):
        return "SWEATSHIRTS AND HOODIES", _plain_pick(
            g,
            "Mens Sweatshirts & Hoodies",
            "Ladies Sweatshirts And Hoodies",
            "Childrens Sweatshirts And Hoodies",
            "UNISEX SWEATSHIRTS & HOODIES",
        )
    if "polo" in cf:
        if "long sleeve" in cf or "longsleeve" in cf:
            return "POLO SHIRTS", _plain_pick(
                g,
                "Mens Long Sleeve Polo Shirts",
                "Ladies Long Sleeve Polo Shirts",
                "Childrens Polo Shirts",
                "Unisex Polo",
            )
        return "POLO SHIRTS", _plain_pick(
            g,
            "MENS SHORT SLEEVE POLO SHIRTS",
            "Ladies Short Sleeve Polo Shirts",
            "Childrens Polo Shirts",
            "Unisex Polo",
        )
    if "tank" in cf or re.search(r"\bvests?\b", cf):
        return "T-SHIRTS", _plain_pick(
            g,
            "Mens Tank Tops, Vest Etc",
            "Ladies Vests, Camisoles, Etc.",
            "Childrens T-Shirt",
            "UNISEX T-SHIRT",
        )
    if (
        "t-shirt" in cf
        or "t shirt" in cf
        or re.search(r"\btee\b", cf)
        or re.search(r"\bt$", cf)
        or " t/" in cf
        or cf.endswith(" t")
    ):
        if "long sleeve" in cf or "longsleeve" in cf or " lsl" in cf:
            return "T-SHIRTS", _plain_pick(
                g,
                "MENS LONG SLEEVE T-SHIRTS",
                "LADIES LONG SLEEVE T-SHIRTS",
                "Childrens T-Shirt",
                "Unisex Long Sleeve T-Shirt",
            )
        return "T-SHIRTS", _plain_pick(
            g,
            "MENS SHORT SLEEVE T-SHIRT",
            "Ladies Short Sleeve T-Shirts",
            "Childrens T-Shirt",
            "UNISEX T-SHIRT",
        )
    if "softshell" in cf or "soft shell" in cf:
        return "OUTERWEAR", _plain_pick(
            g,
            "Mens Softshell",
            "Ladies Softshell",
            "Childrens jackets",
            "Softshell",
        )
    if "fleece" in cf:
        return "OUTERWEAR", _plain_pick(
            g,
            "Mens Fleeces",
            "Ladies Fleeces",
            "Childrens Fleeces",
            "Unisex Fleece",
        )
    if any(tok in cf for tok in ("gilet", "bodywarmer", "body warmer", "body-warmer")):
        return "OUTERWEAR", _plain_pick(
            g,
            "MENS OUTER JACKETS",
            "Ladies Jackets",
            "Childrens jackets",
            "Unisex Jacket",
        )
    if any(
        tok in cf
        for tok in (
            "windbreaker",
            "jacket",
            "parka",
            "anorak",
            "raincoat",
            "shower",
            "bomber",
            "coat",
        )
    ):
        return "OUTERWEAR", _plain_pick(
            g,
            "MENS OUTER JACKETS",
            "Ladies Jackets",
            "Childrens jackets",
            "Unisex Jacket",
        )
    if any(tok in cf for tok in ("jogger", "jog pant", "jogpant", "sweatpant")) or re.search(
        r"\b(trousers?|pants)\b", cf
    ):
        return "TROUSERS & JOGPANTS", _plain_pick(
            g,
            "MENS TROUSERS AND JOGPANTS",
            "Ladies Trousers And Jog Pants",
            "Childrens Trousers And Jogpants",
            "UNISEX TROUSERS & JOGPANTS",
        )
    if re.search(r"\bshorts\b", cf) and "sleeve" not in cf:
        return "TROUSERS & JOGPANTS", _plain_pick(
            g,
            "Mens Shorts",
            "Ladies Shorts",
            "Childrens Trousers And Jogpants",
            "Mens Shorts",
        )
    if re.search(r"\bdress\b", cf):
        return "Corporate Wear", "Ladies Dress"
    if re.search(r"\bskirt\b", cf):
        return "Corporate Wear", "Ladies Skirts"
    if any(tok in cf for tok in ("apron", "tabard")):
        return "Hospitallity", "Aprons And Tabards"
    if "tunic" in cf:
        return "Hospitallity", "Ladies Tunic" if g != GENDER_MENS else "Aprons And Tabards"
    if "chef" in cf:
        return "Hospitallity", _plain_pick(
            g,
            "Unisex Chefswear",
            "Ladies Chefswear",
            "Unisex Chefswear",
            "Unisex Chefswear",
        )
    if "bib" in cf or "bodysuit" in cf or "body suit" in cf or "romper" in cf:
        return "Babywear", "Baby And Toddlerwear"
    if any(tok in cf for tok in ("knit", "jumper", "cardigan", "sweater")) and "sweatshirt" not in cf:
        return "Knitwear", _plain_pick(
            g,
            "Men's Knitwear",
            "Ladies Knitwear",
            "Men's Knitwear",
            "Men's Knitwear",
        )
    if "midlayer" in cf or "mid layer" in cf:
        return "OUTERWEAR", "Mens Midlayer"
    if any(tok in cf for tok in ("boot", "shoe", "footwear", "trainer")):
        return "Footwear", "Footwear"
    if "glove" in cf:
        return "Accessories", "Gloves"
    if "sock" in cf:
        return "Accessories", "Socks"
    if "poplin" in cf or "oxford" in cf or re.search(r"\bshirts?\b", cf):
        return "Shirts & Blouses", _plain_pick(
            g,
            "Mens Shirts",
            "Ladies Shirts",
            "Mens Shirts",
            "Mens Shirts",
        )
    if "wrap" in cf or "keyring" in cf or "key ring" in cf:
        return "Accessories", "Accessories"
    return "Accessories", "Accessories"
