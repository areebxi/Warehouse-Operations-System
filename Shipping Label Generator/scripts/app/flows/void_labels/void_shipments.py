from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.base import Provider
from scripts.app.util.retries import call_with_retries

if TYPE_CHECKING:
    from scripts.app.logging.orders_audit import OrderAuditLogger


@dataclass(frozen=True)
class VoidResult:
    order_number: str
    attempted: int
    voided: int
    reason: str | None = None


async def void_for_order(
    *,
    cfg: AppConfig,
    provider: Provider,
    log: JsonlLogger,
    order_number: str,
    max_shipments_per_order: int | None = None,
    audit: OrderAuditLogger | None = None,
) -> VoidResult:
    try:
        orders = await call_with_retries(
            cfg=cfg,
            log=log,
            op="lookup_orders",
            op_kind="request",
            fn=lambda: provider.lookup_orders(order_number),
            extra={"order_number": order_number},
        )
        if not orders:
            if audit is not None:
                audit.record(outcome="void_skipped", order_number=order_number, reason="order not found")
            return VoidResult(order_number=order_number, attempted=0, voided=0, reason="order not found")

        attempted = 0
        voided = 0
        for o in orders:
            # For parity with the legacy behavior:
            # - single-void mode fetches only 1 shipment
            # - all-void mode fetches up to 100 shipments
            page_size = 1 if max_shipments_per_order == 1 else 100
            active = await call_with_retries(
                cfg=cfg,
                log=log,
                op="list_shipments",
                op_kind="request",
                fn=lambda o=o, page_size=page_size: provider.list_shipments(o.orderId, include_voided=False, page_size=page_size),
                extra={"order_number": order_number, "orderId": o.orderId, "include_voided": False},
            )
            if max_shipments_per_order is not None:
                active = active[: max(0, int(max_shipments_per_order))]

            for s in active:
                attempted += 1
                try:
                    await call_with_retries(
                        cfg=cfg,
                        log=log,
                        op="void_label",
                        op_kind="request",
                        fn=lambda s=s: provider.void_label(s.shipmentId),
                        extra={"order_number": order_number, "orderId": o.orderId, "shipmentId": s.shipmentId},
                    )
                    voided += 1
                    log.info(
                        "void_shipment_success",
                        extra={"order_number": order_number, "orderId": o.orderId, "shipmentId": s.shipmentId},
                    )
                    if audit is not None:
                        audit.record(
                            outcome="void_success",
                            order_number=order_number,
                            shipstation_order_id=str(o.orderId),
                            shipment_id=str(s.shipmentId),
                            carrier_code=s.carrierCode or "",
                            service_code=s.serviceCode or "",
                            package_code=s.packageCode or "",
                        )
                except Exception as e:
                    log.error(
                        "void_shipment_failed",
                        extra={"order_number": order_number, "orderId": o.orderId, "shipmentId": s.shipmentId},
                        exc=e,
                    )
                    if audit is not None:
                        audit.record(
                            outcome="void_failed",
                            order_number=order_number,
                            shipstation_order_id=str(o.orderId),
                            shipment_id=str(s.shipmentId),
                            carrier_code=s.carrierCode or "",
                            service_code=s.serviceCode or "",
                            package_code=s.packageCode or "",
                            reason=str(e),
                        )

        if attempted == 0:
            if audit is not None:
                audit.record(outcome="void_skipped", order_number=order_number, reason="no active shipments")
            return VoidResult(order_number=order_number, attempted=0, voided=0, reason="no active shipments")
        return VoidResult(order_number=order_number, attempted=attempted, voided=voided)
    except Exception as e:
        log.error("void_order_failed", extra={"order_number": order_number}, exc=e)
        if audit is not None:
            audit.record(outcome="void_failed", order_number=order_number, reason=str(e))
        return VoidResult(order_number=order_number, attempted=0, voided=0, reason=str(e))

