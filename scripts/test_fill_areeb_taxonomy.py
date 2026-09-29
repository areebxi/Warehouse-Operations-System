"""ponytail: Areeb maps — fails if BTC/Uneek/CL standard joins drift."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.areeb_taxonomy import (
    AreebCatalogs,
    apply_areeb,
    apply_blank_only,
    leftover_cl,
    load_btc_into,
    load_uneek_into,
    plain_leftover,
)


def _btc_row(**kwargs: str) -> dict[str, str]:
    base = {
        "UID": "",
        "SPC": "",
        "Department": "",
        "Sub Department": "",
        "Brand": "",
        "Description": "",
    }
    base.update(kwargs)
    return base


def _uneek_row(**kwargs: str) -> dict[str, str]:
    base = {
        "Short Code": "",
        "Product Code": "",
        "Category": "",
        "Product Name": "",
        "Full Description": "",
        "Gender": "",
    }
    base.update(kwargs)
    return base


def catalogs() -> AreebCatalogs:
    cat = AreebCatalogs()
    load_btc_into(
        cat,
        [
            _btc_row(
                UID="3264",
                SPC="61082",
                Department="T-Shirts",
                **{"Sub Department": "Mens Short Sleeve T-Shirt"},
                Brand="Fruit Of The Loom",
                Description="Men's Original T-Shirt",
            )
        ],
    )
    load_uneek_into(
        cat,
        [
            _uneek_row(
                **{"Short Code": "UC104"},
                **{"Product Code": "UC104"},
                Category="T-Shirts",
                **{"Product Name": "Classic T"},
                **{"Full Description": "Uneek classic tee"},
                Gender="Mens",
            ),
            _uneek_row(
                **{"Short Code": "805YWSM"},
                **{"Product Code": "UC805"},
                Category="",
                **{"Product Name": "Hi-Viz Polo Shirt"},
                **{"Full Description": "UC805 - Yellow - Small - Hi-Viz Polo Shirt"},
                Gender="Unisex",
            ),
        ],
    )
    return cat


def main() -> None:
    cat = catalogs()

    btc = cat.classify_plain("3264")
    assert btc.source == "btc_uid"
    assert btc.category == "T-Shirts"
    assert btc.product_type == "Mens Short Sleeve T-Shirt"
    assert btc.product_style == "Fruit Of The Loom"
    assert btc.department == "Men's Original T-Shirt"

    uneek = cat.classify_plain("UC104")
    assert uneek.source == "uneek_short"
    assert uneek.category == "T-Shirts"
    assert uneek.product_type == "Classic T"
    assert uneek.product_style == "Uneek classic tee"
    assert uneek.department == "Mens"

    hole = cat.classify_plain(
        "805YWSM",
        product_code="UC805",
        brand="Uneek",
        description="Hi-Viz Polo Shirt",
    )
    assert hole.source == "uneek_short"
    assert hole.category == "Safetywear"
    assert hole.product_type == "Hi-Viz Polo Shirt"
    assert hole.department == "Unisex"

    miss = cat.classify_plain("no-such-sku")
    assert not miss.any_filled()
    assert miss.source == ""

    spc = cat.classify_plain("no-such-sku", product_code="61082")
    assert spc.source == "btc_spc"
    assert spc.category == "T-Shirts"
    assert spc.product_style == "Fruit Of The Loom"

    left = cat.classify_plain(
        "no-such-sku",
        product_code="",
        brand="B&C",
        description="Women's Slim Fit Tee",
    )
    assert left.source == "plain_leftover"
    assert left.category == "T-SHIRTS"
    assert left.product_type == "Ladies Short Sleeve T-Shirts"
    assert left.product_style == "B&C"
    assert left.department == "Women's Slim Fit Tee"

    uid_wins = cat.classify_plain(
        "3264",
        product_code="61082",
        brand="ignored",
        description="ignored tee",
    )
    assert uid_wins.source == "btc_uid"

    hoodie = plain_leftover(
        brand="Bella",
        description="Canvas Unisex Poly-Cotton Fleece Full-Zip Hoodie",
    )
    assert hoodie.category == "SWEATSHIRTS AND HOODIES"
    assert hoodie.product_type == "UNISEX SWEATSHIRTS & HOODIES"
    assert hoodie.product_style == "Bella"

    kids = plain_leftover(brand="B&C", description="Kid's Sirocco Lightweight Windbreaker")
    assert kids.category == "OUTERWEAR"
    assert kids.product_type == "Childrens jackets"
    assert kids.department == "Kid's Sirocco Lightweight Windbreaker"

    cap = plain_leftover(brand="Beechfield", description="Teamwear Competition Cap")
    assert cap.category == "HEADWEAR"
    assert cap.product_type == "Caps & Hats Etc"

    bag = plain_leftover(brand="Bagbase", description="Bagbase Original Fashion Backpack")
    assert bag.category == "Bags"

    girl_tee = plain_leftover(brand="Fruit Of The Loom", description="Fruit Of The Loom Girl's Iconic 150 T")
    assert girl_tee.product_type == "Childrens T-Shirt"

    pack = cat.classify_packs(item1_sku="3264", product_code="x", channel_child_sku="SET1")
    assert pack.source == "btc_uid"
    pack_spc = cat.classify_packs(item1_sku="", product_code="61082", channel_child_sku="")
    assert pack_spc.source == "btc_spc"
    assert pack_spc.category == "T-Shirts"

    # CL never copies BTC/Uneek. Same SKU still uses Gender Apparel.
    cl_ignore_btc = cat.classify_cl(
        {"Supplier SKU": "3264", "Custom Label": "M55-3264", "Gender Apparel": "Mens-T-Shirt"}
    )
    assert cl_ignore_btc.source == "cl_standard"
    assert cl_ignore_btc.department == "Mens"
    assert cl_ignore_btc.product_style == "Standard"

    cl_ignore_uneek = cat.classify_cl(
        {"Supplier SKU": "", "Custom Label": "UC104", "Gender Apparel": "Uneek Classic T-shirt"}
    )
    assert cl_ignore_uneek.source == "cl_standard"
    assert cl_ignore_uneek.category == "T-Shirts"
    assert cl_ignore_uneek.product_style == "Classic"
    assert cl_ignore_uneek.department == "Mens"

    tee = leftover_cl({"Gender Apparel": "Mens-T-Shirt", "Brand": "Gildan"})
    assert tee.source == "cl_standard"
    assert tee.category == "T-Shirts"
    assert tee.product_type == "Short Sleeve T-Shirt"
    assert tee.product_style == "Standard"
    assert tee.department == "Mens"

    ladies_hoodie = leftover_cl({"Gender Apparel": "Womens-Hoodie"})
    assert ladies_hoodie.category == "Sweatshirts & Hoodies"
    assert ladies_hoodie.product_type == "Hoodie"
    assert ladies_hoodie.product_style == "Standard"
    assert ladies_hoodie.department == "Womens"

    gildan = leftover_cl({"Gender Apparel": "GILDAN Heavy Cotton Adult T-Shirt"})
    assert gildan.product_style == "Heavy Cotton"
    assert gildan.department == "Mens"

    sticker = leftover_cl({"Gender Apparel": "Sticker", "Brand": "ignored"})
    assert sticker.category == "Stickers"
    assert sticker.product_type == "Sticker"
    assert sticker.product_style == "Standard"
    assert sticker.department == "General"

    iron = leftover_cl({"Gender Apparel": "DTF-IronOn-A4"})
    assert iron.category == "Iron-On"
    assert iron.product_type == "Iron-On Transfer"
    assert iron.product_style == "A4"
    assert iron.department == "General"

    bag = leftover_cl({"Gender Apparel": "BG-BG125J"})
    assert bag.category == "Bags"
    assert bag.product_style == "Junior Fashion Backpack"
    assert bag.department == "General"

    combo = leftover_cl({"Gender Apparel": "Kids-T-Shirt-Hoodie"})
    assert combo.category == "Sets"
    assert combo.department == "Kids"

    unknown = leftover_cl({"Gender Apparel": "no-such-ga", "Brand": "X"})
    assert not unknown.any_filled()

    fotl = leftover_cl({"Gender Apparel": "FOTL Mens Valueweight T", "Brand": "ignored"})
    assert fotl.category == "T-Shirts"
    assert fotl.product_style == "Valueweight"
    assert fotl.department == "Mens"

    crew = leftover_cl({"Gender Apparel": "GILDAN Heavy Blend Adult Crewneck Sweatshirt"})
    assert crew.category == "Sweatshirts & Hoodies"
    assert crew.product_style == "Heavy Blend"
    assert crew.department == "Mens"

    hiviz = leftover_cl({"Gender Apparel": "Uneek Hi Viz Short Sleeve Polo Shirt"})
    assert hiviz.category == "Polo Shirts"
    assert hiviz.department == "Unisex"

    yoko = leftover_cl({"Gender Apparel": "Yoko Hi-Vis Class 2 Waistcoat"})
    assert yoko.category == "Safetywear"
    assert yoko.product_style == "Class 2"
    assert yoko.department == "Unisex"

    cl_left = cat.classify_cl(
        {
            "Supplier SKU": "",
            "Custom Label": "M-T-BLK-M",
            "Brand": "Gildan",
            "Gender Apparel": "Mens-T-Shirt",
        }
    )
    assert cl_left.source == "cl_standard"
    assert cl_left.product_style == "Standard"
    assert cl_left.department == "Mens"

    overwrite = apply_areeb(
        {
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "",
            "Product Style (Areeb)": "",
            "Department (Areeb)": "Mens-T-Shirt",
        },
        tee,
    )
    assert overwrite.get("Department (Areeb)") == "Mens"
    assert overwrite.get("Product Style (Areeb)") == "Standard"

    invented = leftover_cl({"Gender Apparel": "Mens UniqueWidget T-Shirt"})
    assert invented.product_style == ""
    cleared = apply_areeb(
        {
            "Category (Areeb)": "T-Shirts",
            "Product Type (Areeb)": "Short Sleeve T-Shirt",
            "Product Style (Areeb)": "UniqueWidget",
            "Department (Areeb)": "Mens",
        },
        invented,
    )
    assert cleared.get("Product Style (Areeb)") == ""

    blank_only = apply_blank_only(
        {"Category (Areeb)": "", "Product Type (Areeb)": "keep"},
        btc,
    )
    assert "Category (Areeb)" in blank_only
    assert "Product Type (Areeb)" not in blank_only

    print("areeb taxonomy ok")


if __name__ == "__main__":
    main()
