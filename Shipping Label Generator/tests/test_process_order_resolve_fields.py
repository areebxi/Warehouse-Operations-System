from __future__ import annotations

import os

import pytest

from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.process_order import _resolve_fields
from scripts.app.models.order import Order


def test_resolve_fields_uses_provider_default_carrier_and_maps_service() -> None:
    cfg = AppConfig(
        provider_name="real",
        raw={
            "provider": {"default_carrier": "royal_mail", "default_package": "large_letter"},
            "service_map": {
                "royal_mail": [
                    {"match": "tracked 48", "code": "rm_tracked_48"},
                ]
            },
        },
    )
    o = Order(
        orderId=1,
        orderNumber="A1",
        carrierCode=None,
        serviceCode=None,
        packageCode=None,
        requestedShippingService="UK Tracked 48",
    )
    carrier, service, package = _resolve_fields(cfg=cfg, order=o, shipment_fields={}, process_number="1")
    assert carrier == "royal_mail"
    assert service == "rm_tracked_48"
    assert package == "large_letter"


def test_resolve_fields_raises_clear_error_when_carrier_missing_everywhere() -> None:
    cfg = AppConfig(provider_name="real", raw={"provider": {}, "service_map": {}})
    o = Order(orderId=1, orderNumber="A1", requestedShippingService="Tracked 48")
    with pytest.raises(ValueError) as e:
        _resolve_fields(cfg=cfg, order=o, shipment_fields={}, process_number="1")
    assert "missing carrierCode" in str(e.value)


def test_resolve_fields_rejects_mock_carrier_in_non_test_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHIPPING_TEST_MODE", raising=False)
    cfg = AppConfig(provider_name="real", raw={"provider": {"default_carrier": "mock_carrier"}, "service_map": {}})
    o = Order(orderId=1, orderNumber="A1", requestedShippingService="Tracked 48")
    with pytest.raises(ValueError) as e:
        _resolve_fields(cfg=cfg, order=o, shipment_fields={}, process_number="1")
    assert "mock carrierCode detected" in str(e.value)


def test_resolve_fields_allows_mock_carrier_in_test_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SHIPPING_TEST_MODE", "1")
    cfg = AppConfig(provider_name="real", raw={"provider": {"default_carrier": "mock_carrier"}, "service_map": {}})
    o = Order(orderId=1, orderNumber="A1", requestedShippingService="Tracked 48")
    # Will still fail later because there's no service mapping, but it should NOT fail due to the mock guard.
    with pytest.raises(ValueError) as e:
        _resolve_fields(cfg=cfg, order=o, shipment_fields={}, process_number="1")
    assert "mock carrierCode detected" not in str(e.value)

