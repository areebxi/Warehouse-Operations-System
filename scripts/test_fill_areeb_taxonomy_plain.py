"""Plain/BTC/Uneek assert cases."""
from __future__ import annotations

from shared.areeb_taxonomy import leftover_cl, plain_leftover

def assert_plain_cases(cat) -> None:

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

