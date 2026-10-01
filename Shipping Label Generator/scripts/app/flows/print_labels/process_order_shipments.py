from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.config.load import AppConfig
from app.flows.print_labels.order_audit import _audit_step
from app.flows.print_labels.order_retries import _timed_call_with_retries
from app.logging.jsonl import JsonlLogger
from app.models.label import Label
from app.models.order import Order
from app.providers.base import Provider
from app.rules.selection import select_shipments

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger


async def load_shipments_and_maybe_reuse(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name: str,
    selected: Order,
    audit: OrderAuditLogger | None,
) -> tuple[Any, Label | None, dict[str, str | None]]:
    """List shipments and attempt non-voided label reuse. Returns (sel_ship, label, fields)."""
    all_shipments = await _timed_call_with_retries(
        cfg=cfg,
        log=log,
        op="list_shipments",
        op_kind="request",
        fn=lambda: provider.list_shipments(selected.orderId, include_voided=True, page_size=100),
        extra={
            "order_number": order_number,
            "process_number": process_number,
            "orderId": selected.orderId,
            "include_voided": True,
        },
    )
    sel_ship = select_shipments(all_shipments)
    _audit_step(
        audit,
        outcome="print_shipments_loaded",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        shipstation_order_id=str(selected.orderId),
        shipment_count=int(len(sel_ship.shipments)),
        used_voided=bool(sel_ship.used_voided),
    )
    if sel_ship.used_voided and sel_ship.shipments:
        log.warning(
            "print_using_voided_shipments",
            extra={
                "order_number": order_number,
                "process_number": process_number,
                "orderId": selected.orderId,
            },
        )
        _audit_step(
            audit,
            outcome="print_using_voided_shipments",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            shipstation_order_id=str(selected.orderId),
            shipment_id=str(sel_ship.shipments[0].shipmentId),
        )

    label: Label | None = None
    shipment_fields: dict[str, str | None] = {
        "carrierCode": None,
        "serviceCode": None,
        "packageCode": None,
    }
    if sel_ship.shipments:
        s0 = sel_ship.shipments[0]
        shipment_fields = {
            "carrierCode": s0.carrierCode,
            "serviceCode": s0.serviceCode,
            "packageCode": s0.packageCode,
        }

    if sel_ship.shipments and not sel_ship.used_voided:
        try:
            fetched = await _timed_call_with_retries(
                cfg=cfg,
                log=log,
                op="fetch_label",
                op_kind="label",
                fn=lambda: provider.fetch_label(sel_ship.shipments[0].shipmentId),
                extra={
                    "order_number": order_number,
                    "process_number": process_number,
                    "orderId": selected.orderId,
                    "shipmentId": sel_ship.shipments[0].shipmentId,
                },
            )
            if fetched and fetched.labelData:
                label = fetched
                _audit_step(
                    audit,
                    outcome="print_label_reused",
                    order_number=order_number,
                    process_number=process_number,
                    customer_name=customer_name,
                    shipstation_order_id=str(selected.orderId),
                    shipment_id=str(sel_ship.shipments[0].shipmentId),
                    carrier_code=shipment_fields.get("carrierCode") or "",
                    service_code=shipment_fields.get("serviceCode") or "",
                    package_code=shipment_fields.get("packageCode") or "",
                )
        except Exception:
            log.warning(
                "print_fetch_label_failed",
                extra={"order_number": order_number, "process_number": process_number},
            )
            _audit_step(
                audit,
                outcome="print_label_fetch_failed",
                order_number=order_number,
                process_number=process_number,
                customer_name=customer_name,
                shipstation_order_id=str(selected.orderId),
                shipment_id=str(sel_ship.shipments[0].shipmentId),
            )

    return sel_ship, label, shipment_fields
