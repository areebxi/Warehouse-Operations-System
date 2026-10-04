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

def assert_cl_cases(cat) -> None:
    # CL never copies BTC/Uneek. Same SKU still uses Gender Apparel.
    cl_ignore_btc = cat.classify_cl(
        {"Supplier_SKU": "3264", "Custom_Label": "M55-3264", "Gender_Apparel": "Mens-T-Shirt"}
    )
    assert cl_ignore_btc.source == "cl_standard"
    assert cl_ignore_btc.department == "Mens"
    assert cl_ignore_btc.product_style == "Standard"

    cl_ignore_uneek = cat.classify_cl(
        {"Supplier_SKU": "", "Custom_Label": "UC104", "Gender_Apparel": "Uneek Classic T-shirt"}
    )
    assert cl_ignore_uneek.source == "cl_standard"
    assert cl_ignore_uneek.category == "T-Shirts"
    assert cl_ignore_uneek.product_style == "Classic"
    assert cl_ignore_uneek.department == "Mens"

    tee = leftover_cl({"Gender_Apparel": "Mens-T-Shirt", "Brand": "Gildan"})
    assert tee.source == "cl_standard"
    assert tee.category == "T-Shirts"
    assert tee.product_type == "Short Sleeve T-Shirt"
    assert tee.product_style == "Standard"
    assert tee.department == "Mens"

    ladies_hoodie = leftover_cl({"Gender_Apparel": "Womens-Hoodie"})
    assert ladies_hoodie.category == "Sweatshirts & Hoodies"
    assert ladies_hoodie.product_type == "Hoodie"
    assert ladies_hoodie.product_style == "Standard"
    assert ladies_hoodie.department == "Womens"

    gildan = leftover_cl({"Gender_Apparel": "GILDAN Heavy Cotton Adult T-Shirt"})
    assert gildan.product_style == "Heavy Cotton"
    assert gildan.department == "Mens"

    sticker = leftover_cl({"Gender_Apparel": "Sticker", "Brand": "ignored"})
    assert sticker.category == "Stickers"
    assert sticker.product_type == "Sticker"
    assert sticker.product_style == "Standard"
    assert sticker.department == "General"

    iron = leftover_cl({"Gender_Apparel": "DTF-IronOn-A4"})
    assert iron.category == "Iron-On"
    assert iron.product_type == "Iron-On Transfer"
    assert iron.product_style == "A4"
    assert iron.department == "General"

    bag = leftover_cl({"Gender_Apparel": "BG-BG125J"})
    assert bag.category == "Bags"
    assert bag.product_style == "Junior Fashion Backpack"
    assert bag.department == "General"

    combo = leftover_cl({"Gender_Apparel": "Kids-T-Shirt-Hoodie"})
    assert combo.category == "Sets"
    assert combo.department == "Kids"

    unknown = leftover_cl({"Gender_Apparel": "no-such-ga", "Brand": "X"})
    assert not unknown.any_filled()

    fotl = leftover_cl({"Gender_Apparel": "FOTL Mens Valueweight T", "Brand": "ignored"})
    assert fotl.category == "T-Shirts"
    assert fotl.product_style == "Valueweight"
    assert fotl.department == "Mens"

    crew = leftover_cl({"Gender_Apparel": "GILDAN Heavy Blend Adult Crewneck Sweatshirt"})
    assert crew.category == "Sweatshirts & Hoodies"
    assert crew.product_style == "Heavy Blend"
    assert crew.department == "Mens"

    hiviz = leftover_cl({"Gender_Apparel": "Uneek Hi Viz Short Sleeve Polo Shirt"})
    assert hiviz.category == "Polo Shirts"
    assert hiviz.department == "Unisex"

    yoko = leftover_cl({"Gender_Apparel": "Yoko Hi-Vis Class 2 Waistcoat"})
    assert yoko.category == "Safetywear"
    assert yoko.product_style == "Class 2"
    assert yoko.department == "Unisex"

    cl_left = cat.classify_cl(
        {
            "Supplier_SKU": "",
            "Custom_Label": "M-T-BLK-M",
            "Brand": "Gildan",
            "Gender_Apparel": "Mens-T-Shirt",
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

    invented = leftover_cl({"Gender_Apparel": "Mens UniqueWidget T-Shirt"})
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
        cat.classify_plain("3264"),
    )
    assert "Category (Areeb)" in blank_only
    assert "Product Type (Areeb)" not in blank_only

    print("areeb taxonomy ok")

