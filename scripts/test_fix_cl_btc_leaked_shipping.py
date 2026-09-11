"""ponytail: leaked Package Type / Weight / Service must not stay in BTC columns."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from fix_cl_btc_leaked_shipping import plan_row


def test_copied_shipping_trio_replaced_from_supplier() -> None:
    patch = plan_row(
        {
            "BTC SKU": "Large Letter",
            "BTC Product Code": "186",
            "BTC Supplier Stock": "Royal Mail48",
            "Package Type": "Large Letter",
            "Weight": "186",
            "Service": "Royal Mail48",
            "Supplier Name": "BTC Activewear",
            "Supplier SKU": "3264",
            "Supplier Product Code": "61082",
            "Supplier Stock": "",
        }
    )
    assert patch["BTC SKU"] == "3264"
    assert patch["BTC Product Code"] == "61082"
    assert patch["BTC Supplier Stock"] == ""
    assert "Package Type" not in patch
    assert "Weight" not in patch
    assert "Service" not in patch


def test_restores_orphan_package_weight_service() -> None:
    patch = plan_row(
        {
            "BTC SKU": "Large Letter",
            "BTC Product Code": "195",
            "BTC Supplier Stock": "Royal Mail48",
            "Package Type": "",
            "Weight": "",
            "Service": "",
            "Supplier Name": "BTC Activewear",
            "Supplier SKU": "3265",
            "Supplier Product Code": "61082",
            "Supplier Stock": "",
        }
    )
    assert patch["Package Type"] == "Large Letter"
    assert patch["Weight"] == "195"
    assert patch["Service"] == "Royal Mail48"
    assert patch["BTC SKU"] == "3265"
    assert patch["BTC Product Code"] == "61082"


def test_weight_only_in_product_code() -> None:
    patch = plan_row(
        {
            "BTC SKU": "",
            "BTC Product Code": "360",
            "BTC Supplier Stock": "",
            "Package Type": "",
            "Weight": "360",
            "Service": "",
            "Supplier Name": "BTC Activewear",
            "Supplier SKU": "76859",
            "Supplier Product Code": "BG125J",
            "Supplier Stock": "",
        }
    )
    assert patch == {"BTC Product Code": "BG125J"}


def test_keeps_real_uid_and_spc() -> None:
    row = {
        "BTC SKU": "14801",
        "BTC Product Code": "61028",
        "BTC Supplier Stock": "",
        "Package Type": "Large Letter",
        "Weight": "186",
        "Service": "Royal Mail48",
        "Supplier Name": "BTC Activewear",
        "Supplier SKU": "14801",
        "Supplier Product Code": "61028",
        "Supplier Stock": "",
    }
    assert plan_row(row) == {}


def test_parcel_and_crl_service() -> None:
    patch = plan_row(
        {
            "BTC SKU": "Parcel",
            "BTC Product Code": "271",
            "BTC Supplier Stock": "Royal Mail 48 - CRL",
            "Package Type": "Parcel",
            "Weight": "271",
            "Service": "Royal Mail 48 - CRL",
            "Supplier Name": "BTC Activewear",
            "Supplier SKU": "999",
            "Supplier Product Code": "SS10",
            "Supplier Stock": "12",
        }
    )
    assert patch["BTC SKU"] == "999"
    assert patch["BTC Product Code"] == "SS10"
    assert patch["BTC Supplier Stock"] == "12"


if __name__ == "__main__":
    test_copied_shipping_trio_replaced_from_supplier()
    test_restores_orphan_package_weight_service()
    test_weight_only_in_product_code()
    test_keeps_real_uid_and_spc()
    test_parcel_and_crl_service()
    print("ok")
