from __future__ import annotations

from scripts.app.rules.service_map import map_service_code


def test_service_map_first_match_wins() -> None:
    cfg_raw = {
        "service_map": {
            "royal_mail": [
                {"match": "tracked", "code": "RM_TRK"},
                {"match": "tracked 48", "code": "RM_TRK48"},
            ]
        }
    }

    # "tracked" appears first, so it wins even though "tracked 48" is more specific.
    code = map_service_code(cfg_raw=cfg_raw, carrier="Royal Mail", requested_shipping_service="Tracked 48 Large Letter")
    assert code == "RM_TRK"


def test_service_map_none_when_missing() -> None:
    cfg_raw = {"service_map": {"royal_mail": [{"match": "x", "code": "Y"}]}}
    assert map_service_code(cfg_raw=cfg_raw, carrier="royal mail", requested_shipping_service=None) is None
    assert map_service_code(cfg_raw=cfg_raw, carrier="royal mail", requested_shipping_service="something else") is None

