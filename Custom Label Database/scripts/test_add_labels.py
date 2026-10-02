"""ponytail: add_labels C800T optional-P / acrylic size / leading P# Customise."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from add_labels import (  # noqa: E402
    RE_ACRYLIC_SIZE,
    RE_AMZ_SIZE_CODE,
    RE_BAG_COLOUR,
    RE_C800T_AGE,
    RE_GILDAN_5000,
    RE_MOCK_P_UID,
    RE_TRANSFER,
    RE_WAREHOUSE_GARMENT,
    _ACRYLIC_PAPER,
    _BAG_COLOUR,
    _WAREHOUSE_GA,
    _age_to_size,
    _peer_keys_for_label,
    _sticker_size,
    hyphen_tshirt_in_slug,
    label_from_input,
)
from fill_from_seeds import customise_for_label  # noqa: E402


def main() -> None:
    assert label_from_input("11828ALG-M281-P5-C800T-30-6>12", from_sku=True) == (
        "M281-P5-C800T-30-6>12"
    )
    assert label_from_input("10182ALG-M281-C800T-30-3>6", from_sku=True) == (
        "M281-C800T-30-3>6"
    )
    assert label_from_input("32BLG-P5-ACPPLQ-A410-PB", from_sku=True) == (
        "P5-ACPPLQ-A410-PB"
    )
    assert RE_C800T_AGE.match("M281-P5-C800T-30-6>12")
    assert RE_C800T_AGE.match("M281-C800T-30-3>6")
    assert _age_to_size("6>12") == "6-12 Months"
    keys = _peer_keys_for_label("M281-C800T-30-3>6")
    assert any(k.startswith("__prefix__:m281-p5-c800t-") for k in keys)
    m = RE_ACRYLIC_SIZE.search("P5-ACPPLQ-A410-PB")
    assert m is not None and m.group(1) == "4" and m.group(2) == "10"
    a6 = RE_ACRYLIC_SIZE.search("P5-ACPPLQ-A625-PB")
    assert a6 is not None and a6.group(1) == "6" and a6.group(2) == "25"
    a415 = RE_ACRYLIC_SIZE.search("P5-ACPPLQ-A415-PB")
    assert a415 is not None and a415.group(1) == "4" and a415.group(2) == "15"
    a710 = RE_ACRYLIC_SIZE.search("ACPPLQ-A710-PB")
    assert a710 is not None and a710.group(1) == "7" and a710.group(2) == "10"
    assert _ACRYLIC_PAPER["7"] == ("A7", "74", "105")
    assert RE_AMZ_SIZE_CODE.match("ARM-BBe-C1-D6-EF")
    assert any(
        k.startswith("__prefix__:arm-bbe-") for k in _peer_keys_for_label("ARM-BBe-C1-D6-EF")
    )
    assert "__suffix__:-d6-ef" in _peer_keys_for_label("ARM-BBe-C1-D6-EF")
    assert "a515-photo" in _peer_keys_for_label("P5-ACPPLQ-A410-PB")
    assert "dtf-ironon-a4" in _peer_keys_for_label("M263-P5-DTF-IronOn-A4")
    assert "stckr-m(30cmx30cm)" in _peer_keys_for_label("STICKERS-M(30cmx30cm)")
    assert "f4-m-t-nvy-m" in _peer_keys_for_label("F4-M-T-NVY-M-Yes")
    assert customise_for_label("P5-ACPPLQ-A410-PB") == "Yes"
    assert customise_for_label("A515") == "Yes"
    assert customise_for_label("A515-PHOTO") == ""
    assert customise_for_label("M260-P3-3265") == "Yes"
    assert customise_for_label("M55-120852") == ""
    assert RE_BAG_COLOUR.match("BG-BG140S-ClaRdOW-O/S-YES")
    assert _BAG_COLOUR["clardow"] == "Classic Red-Off White"
    assert _BAG_COLOUR["clapk"] == "Classic Pink"
    assert RE_MOCK_P_UID.match("N01-P7-67361")
    assert RE_MOCK_P_UID.match("M407-P1-1D114")
    assert "__suffix__:-67361" in _peer_keys_for_label("N01-P7-67361")
    assert "a515-photo" in _peer_keys_for_label("M407-P1-1D114")
    assert any(
        k.startswith("__prefix__:f/b-m-t-nvy-")
        for k in _peer_keys_for_label("F/B-M-T-NVY-S-YES")
    )
    assert any(
        k.startswith("__prefix__:bg-bg140s-")
        for k in _peer_keys_for_label("BG-BG140S-ClaRdOW-O/S-YES")
    )
    assert _sticker_size("50cmx50cm") == "50cm x 50cm"
    assert any(
        k.startswith("__prefix__:stickers-l(")
        for k in _peer_keys_for_label("STICKERS-L(50cmx50cm)-YES")
    )
    assert RE_TRANSFER.match("Transfer-1M-1")
    assert RE_TRANSFER.match("Transfer-3M")
    assert label_from_input("DTF-Transfer-1M-1", from_sku=True) == "Transfer-1M-1"
    assert label_from_input("ACPPLQ-A625-PHOTO", from_sku=True) == "A625-PHOTO"
    assert label_from_input("75931-W-H-BLK-M", from_sku=True) == "W-H-BLK-M"
    assert RE_WAREHOUSE_GARMENT.match("W-H-BLK-M")
    assert RE_WAREHOUSE_GARMENT.match("K-H-DHR-YXS")
    assert _WAREHOUSE_GA[("W", "H")] == "Womens-Hoodie"
    assert "m-h-blk-m" in _peer_keys_for_label("W-H-BLK-M")
    assert label_from_input("128357LG-5000-NAT-S", from_sku=True) == "5000-NAT-S"
    assert RE_GILDAN_5000.match("5000-NAT-S")
    assert RE_GILDAN_5000.match("5000-LPNK-XL")
    assert "a3-5000-nat-s" in _peer_keys_for_label("5000-NAT-S")
    assert hyphen_tshirt_in_slug("Gildan-Heavy-Cotton-Adult-TShirt-Natural") == (
        "Gildan-Heavy-Cotton-Adult-T-Shirt-Natural"
    )
    print("ok")


if __name__ == "__main__":
    main()
