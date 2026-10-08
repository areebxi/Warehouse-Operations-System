"""Runtime self-checks before fill (same asserts as legacy add_labels.main)."""
from __future__ import annotations

from fill_from_seeds import customise_for_label, hyphen_tshirt_in_slug, uid_from_custom_label

from add_labels_parse import (
    RE_BAG_COLOUR,
    RE_BAG_SIZE_YES,
    RE_C800T_AGE,
    RE_GILDAN_5000,
    RE_IRONON,
    RE_TRANSFER,
    RE_WAREHOUSE_GARMENT,
    _BAG_COLOUR,
    _WAREHOUSE_GA,
    _age_to_size,
    _sticker_mm,
    _sticker_size,
    label_from_input,
)
from add_labels_peer_keys import _alias_shirt_colour_label, _peer_keys_for_label


def run_selfchecks() -> None:
    assert uid_from_custom_label("M260-P3-3265") == "3265"
    assert uid_from_custom_label("M281-P5-C800T-30-18-24") == ""
    assert uid_from_custom_label("Transfer-1M-1") == ""
    assert uid_from_custom_label("Transfer-3M") == ""
    assert uid_from_custom_label("208544") == "208544"
    assert label_from_input("10428ALG-M260-P3-3265", from_sku=True) == "M260-P3-3265"
    assert customise_for_label("W101-SkyBe-O/S-Yes") == "Yes"
    assert customise_for_label("M260-P3-3265") == "Yes"
    assert customise_for_label("M55-120852") == ""
    assert _age_to_size("3&gt;6") == "3-6 Months"
    assert _age_to_size("6>12") == "6-12 Months"
    assert RE_C800T_AGE.match("M281-P5-C800T-30-3&gt;6")
    assert RE_C800T_AGE.match("M281-C800T-30-3>6")
    assert RE_C800T_AGE.match("M281-P5-C800T-30-6>12")
    assert customise_for_label("P5-ACPPLQ-A410-PB") == "Yes"
    assert customise_for_label("A515") == "Yes"
    assert customise_for_label("A515-PHOTO") == ""
    assert _alias_shirt_colour_label("M-T-NAV-XL") == "M-T-NVY-XL"
    assert _alias_shirt_colour_label("M-T-PUE-L") == "M-T-PRP-L"
    assert RE_BAG_COLOUR.match("BG-BG140S-ClaRdOW-O/S-YES")
    assert _BAG_COLOUR["clardow"] == "Classic Red-Off White"
    assert _BAG_COLOUR["orn"] == "Orange"
    assert _BAG_COLOUR["brirl"] == "Bright Royal"
    assert _BAG_COLOUR["dusgn"] == "Dusty Green"
    assert _sticker_size("50cmx50cm") == "50cm x 50cm"
    assert _sticker_mm("50cmx50cm") == ("500", "500")
    assert _sticker_mm("20cm x 20cm") == ("200", "200")
    assert RE_IRONON.search("M280-P5-IronOn-A6")
    assert RE_IRONON.search("M280-P5-DTF-IronOn-A6")
    assert RE_BAG_SIZE_YES.match("W415-NAT-L-Yes")
    assert RE_TRANSFER.match("Transfer-1M-1") and RE_TRANSFER.match("Transfer-3M")
    assert label_from_input("DTF-Transfer-1M-1", from_sku=True) == "Transfer-1M-1"
    assert label_from_input("ACPPLQ-A625-PHOTO", from_sku=True) == "A625-PHOTO"
    assert label_from_input("75931-W-H-BLK-M", from_sku=True) == "W-H-BLK-M"
    assert RE_WAREHOUSE_GARMENT.match("W-H-BLK-M")
    assert _WAREHOUSE_GA[("W", "H")] == "Womens-Hoodie"
    assert "m-h-blk-m" in _peer_keys_for_label("W-H-BLK-M")
    assert label_from_input("128357LG-5000-NAT-S", from_sku=True) == "5000-NAT-S"
    assert RE_GILDAN_5000.match("5000-NAT-S") and RE_GILDAN_5000.match("5000-LPNK-XL")
    assert "a3-5000-nat-s" in _peer_keys_for_label("5000-NAT-S")
    assert hyphen_tshirt_in_slug("Gildan-Heavy-Cotton-Adult-TShirt-Natural") == (
        "Gildan-Heavy-Cotton-Adult-T-Shirt-Natural"
    )
