from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar
from app.config.load import AppConfig
from app.flows.print_labels.failures import FailureRow
from app.logging.jsonl import JsonlLogger
from app.models.label import Label
from app.models.order import Order
from app.providers.base import Provider
from app.rules.service_map import carrier_key, map_service_code
from app.rules.order_status import cancelled_order_reason, is_order_cancelled
from app.rules.selection import select_order_candidate, select_shipments
from app.rules.weights import normalize_weight
from app.util.retries import call_with_retries

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
class ServiceCodeResolutionError(ValueError):
    """
    Raised when we cannot determine a ShipStation serviceCode for an order.

    This is intentionally a ValueError so existing failure handling keeps working.
    """

    order_number: str
    process_number: str
    carrier_code: str | None
    requested_shipping_service: str | None
    carrier_key: str | None
    order_service_code: str | None
    shipment_service_code: str | None
    message: str

    def __str__(self) -> str:
        # Keep a single-line reason that is safe for CSV + PDFs.
        return (
            "serviceCode could not be resolved"
            f" (order_number={self.order_number!r}, process_number={self.process_number!r},"
            f" carrierCode={self.carrier_code!r}, carrier_key={self.carrier_key!r},"
            f" requestedShippingService={self.requested_shipping_service!r},"
            f" order.serviceCode={self.order_service_code!r}, shipment.serviceCode={self.shipment_service_code!r};"
            f" {self.message})"
        )
async def _timed_call_with_retries(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    op: str,
    op_kind: str,
    fn: Callable[[], Awaitable[T]],
    extra: dict[str, Any],
) -> T:
    """Wraps call_with_retries and logs elapsed_ms per op (includes retries)."""
    t0 = monotonic()
    try:
        out = await call_with_retries(cfg=cfg, log=log, op=op, op_kind=op_kind, fn=fn, extra=extra)
        log.info(
            "provider_op_timing",
            extra={**extra, "op": op, "elapsed_ms": round((monotonic() - t0) * 1000.0, 2), "ok": True},
        )
        return out
    except Exception:
        log.info(
            "provider_op_timing",
            extra={**extra, "op": op, "elapsed_ms": round((monotonic() - t0) * 1000.0, 2), "ok": False},
        )
        raise
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
def _audit_step(
    audit: OrderAuditLogger | None,
    *,
    outcome: str,
    order_number: str,
    process_number: str,
    customer_name: str = "",
    **fields: Any,
) -> None:
    if audit is None:
        return
    audit.record(
        outcome=outcome,
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        **fields,
    )
