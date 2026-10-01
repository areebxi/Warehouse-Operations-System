from __future__ import annotations

import os
from typing import Any

from app.config.load import AppConfig
from app.flows.print_labels.order_result import ServiceCodeResolutionError
from app.models.order import Order
from app.rules.order_status import is_order_cancelled
from app.rules.selection import select_order_candidate
from app.rules.service_map import carrier_key, map_service_code


def _is_test_mode() -> bool:
    """
    Guardrail to prevent mock/test data leaking into production runs.

    Enable by setting SHIPPING_TEST_MODE=1 (or true/yes/on).
    """
    v = (os.getenv("SHIPPING_TEST_MODE") or "").strip().lower()
    return v in ("1", "true", "yes", "y", "on")

def _extract_total_weight_lb(order: Order) -> float | None:
    total_lb = 0.0
    seen = False
    for it in order.items or []:
        if not isinstance(it, dict):
            continue
        w = it.get("weight")
        u = it.get("weightUnit")
        q = it.get("quantity", 1) or 1
        if w is None or u is None:
            continue
        try:
            wf = float(w)
            qf = float(q)
        except Exception:
            continue
        unit = str(u).strip().lower()
        if unit in ("lb", "lbs", "pound", "pounds"):
            total_lb += wf * qf
            seen = True
        elif unit in ("oz", "ounce", "ounces"):
            total_lb += (wf / 16.0) * qf
            seen = True
    return total_lb if seen else None

def _pick_order_candidate_fast(*, candidates: list[Order], has_active_shipments: dict[int, bool]) -> Order | None:
    """
    Candidate selection optimization:
    - If ShipStation returns exactly one candidate order, skip the extra per-candidate
      /shipments(active, pageSize=1) call and just use it.
    - If there are multiple candidates, preserve the existing "awaiting shipment" selection rules.
    - Cancelled channel orders are never selected.
    """
    if not candidates:
        return None
    shippable = [o for o in candidates if not is_order_cancelled(o)]
    if not shippable:
        return None
    if len(shippable) == 1:
        return shippable[0]
    return select_order_candidate(candidates=shippable, has_active_shipments=has_active_shipments)

def _resolve_fields(
    *,
    cfg: AppConfig,
    order: Order,
    shipment_fields: dict[str, str | None],
    process_number: str = "",
) -> tuple[str, str, str]:
    provider_cfg = cfg.raw.get("provider") or {}
    provider_cfg = provider_cfg if isinstance(provider_cfg, dict) else {}
    default_carrier = str(provider_cfg.get("default_carrier") or "").strip()
    default_package = str(provider_cfg.get("default_package") or "").strip()

    carrier = shipment_fields.get("carrierCode") or order.carrierCode or (default_carrier or None)
    package = shipment_fields.get("packageCode") or order.packageCode or (default_package or None) or "package"
    service = shipment_fields.get("serviceCode") or order.serviceCode

    if not _is_test_mode():
        if carrier and str(carrier).strip().lower().startswith("mock_"):
            raise ServiceCodeResolutionError(
                order_number=str(order.orderNumber),
                process_number=str(process_number or ""),
                carrier_code=str(carrier),
                requested_shipping_service=order.requestedShippingService,
                carrier_key=carrier_key(str(carrier)),
                order_service_code=order.serviceCode,
                shipment_service_code=shipment_fields.get("serviceCode"),
                message="mock carrierCode detected in non-test mode (set SHIPPING_TEST_MODE=1 to allow)",
            )
        if order.requestedShippingService and str(order.requestedShippingService).strip().lower().startswith("mock_"):
            ckey = carrier_key(str(carrier)) if carrier else None
            raise ServiceCodeResolutionError(
                order_number=str(order.orderNumber),
                process_number=str(process_number or ""),
                carrier_code=str(carrier) if carrier else None,
                requested_shipping_service=order.requestedShippingService,
                carrier_key=ckey,
                order_service_code=order.serviceCode,
                shipment_service_code=shipment_fields.get("serviceCode"),
                message="mock requestedShippingService detected in non-test mode (set SHIPPING_TEST_MODE=1 to allow)",
            )

    if not carrier:
        raise ServiceCodeResolutionError(
            order_number=str(order.orderNumber),
            process_number=str(process_number or ""),
            carrier_code=None,
            requested_shipping_service=order.requestedShippingService,
            carrier_key=None,
            order_service_code=order.serviceCode,
            shipment_service_code=shipment_fields.get("serviceCode"),
            message=(
                "missing carrierCode; "
                f"order.carrierCode={order.carrierCode!r}, shipment.carrierCode={shipment_fields.get('carrierCode')!r}, "
                f"provider.default_carrier={default_carrier!r}"
            ),
        )

    if not service:
        service = map_service_code(
            cfg_raw=cfg.raw,
            carrier=str(carrier),
            requested_shipping_service=order.requestedShippingService,
        )

    if not service:
        ckey = carrier_key(str(carrier))
        raise ServiceCodeResolutionError(
            order_number=str(order.orderNumber),
            process_number=str(process_number or ""),
            carrier_code=str(carrier),
            requested_shipping_service=order.requestedShippingService,
            carrier_key=ckey,
            order_service_code=order.serviceCode,
            shipment_service_code=shipment_fields.get("serviceCode"),
            message="no matching service_map entry and no serviceCode on order/shipment",
        )

    return str(carrier), str(service), str(package)

