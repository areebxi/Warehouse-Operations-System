from __future__ import annotations

from scripts.app.rules.weights import normalize_weight


def test_normalize_weight_to_ounces_for_matching_carrier_substring() -> None:
    cfg_raw = {"weight": {"ounce_carriers": ["royal_mail", "stamps_com"]}}
    w, unit = normalize_weight(cfg_raw=cfg_raw, carrier_code="ROYAL_MAIL_tracked", weight=2.5)
    assert w == 2.5 * 16.0
    assert unit == "oz"


def test_normalize_weight_to_pounds_for_other_carriers() -> None:
    cfg_raw = {"weight": {"ounce_carriers": ["royal_mail"]}}
    w, unit = normalize_weight(cfg_raw=cfg_raw, carrier_code="ups_ground", weight=3.0)
    assert w == 3.0
    assert unit == "lb"

