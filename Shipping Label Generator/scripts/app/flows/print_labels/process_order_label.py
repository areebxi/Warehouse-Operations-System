from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.config.load import AppConfig
from app.flows.print_labels.order_audit import _audit_step
from app.flows.print_labels.order_fields import _extract_total_weight_lb, _resolve_fields
from app.flows.print_labels.order_result import OrderResult
from app.flows.print_labels.order_retries import _timed_call_with_retries
from app.flows.print_labels.process_order_shipments import load_shipments_and_maybe_reuse
from app.logging.jsonl import JsonlLogger
from app.models.order import Order
from app.providers.base import Provider
from app.rules.weights import normalize_weight

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger


async def create_or_reuse_label(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name: str,
    selected: Order,
    labels_dir: Path,
    audit: OrderAuditLogger | None,
) -> tuple[OrderResult, dict[str, Any]]:
    """
    Load shipments, reuse or create label, write PDF.

    Returns (success_result, locals_for_error_handler) where the second value
    includes carrier/service/package/shipment_fields for failure paths.
    """
    sel_ship, label, shipment_fields = await load_shipments_and_maybe_reuse(
        cfg=cfg,
        log=log,
        provider=provider,
        process_number=process_number,
        order_number=order_number,
        customer_name=customer_name,
        selected=selected,
        audit=audit,
    )
    reused_label = label is not None

    carrier, service, package = _resolve_fields(
        cfg=cfg, order=selected, shipment_fields=shipment_fields, process_number=process_number
    )
    _audit_step(
        audit,
        outcome="print_service_resolved",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        shipstation_order_id=str(selected.orderId),
        carrier_code=carrier,
        service_code=service,
        package_code=package,
        requested_shipping_service=selected.requestedShippingService or "",
    )
    log.info(
        "service_mapping_resolved",
        extra={
            "order_number": order_number,
            "process_number": process_number,
            "carrierCode": carrier,
            "requestedShippingService": selected.requestedShippingService,
            "serviceCode": service,
            "packageCode": package,
        },
    )

    if label is None:
        weight_lb = _extract_total_weight_lb(selected)
        weight_val: float | None = None
        weight_unit: str | None = None
        if weight_lb is not None:
            weight_val, weight_unit = normalize_weight(
                cfg_raw=cfg.raw, carrier_code=carrier, weight=weight_lb
            )
        _audit_step(
            audit,
            outcome="print_label_creating",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            shipstation_order_id=str(selected.orderId),
            carrier_code=carrier,
            service_code=service,
            package_code=package,
            requested_shipping_service=selected.requestedShippingService or "",
            weight=weight_val,
            weight_unit=weight_unit,
        )
        label = await _timed_call_with_retries(
            cfg=cfg,
            log=log,
            op="create_label",
            op_kind="label",
            fn=lambda: provider.create_label(
                order=selected,
                carrier_code=carrier,
                service_code=service,
                package_code=package,
                ship_date=date.today().isoformat(),
                weight=weight_val,
                weight_unit=weight_unit,
                customer_reference=None,
            ),
            extra={
                "order_number": order_number,
                "process_number": process_number,
                "orderId": selected.orderId,
            },
        )

    from app.pdf.label_decode import write_label_pdf

    out_path = labels_dir / f"{order_number}.pdf"
    write_label_pdf(out_path, label_data_b64=label.labelData)
    shipment_id = ""
    tracking_number = ""
    if sel_ship.shipments:
        shipment_id = str(sel_ship.shipments[0].shipmentId)
    if label.trackingNumber:
        tracking_number = str(label.trackingNumber)
    if audit is not None:
        audit.record(
            outcome="print_success",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            shipstation_order_id=str(selected.orderId),
            carrier_code=carrier,
            service_code=service,
            package_code=package,
            requested_shipping_service=selected.requestedShippingService or "",
            label_source="reused" if reused_label else "created",
            shipment_id=shipment_id,
            tracking_number=tracking_number,
            label_pdf=str(out_path),
        )
    result = OrderResult(
        order_number=order_number,
        process_number=process_number,
        label_pdf_path=out_path,
        failure=None,
        ship_from=selected.shipFromName,
    )
    ctx = {
        "selected": selected,
        "shipment_fields": shipment_fields,
        "carrier": carrier,
        "service": service,
        "package": package,
    }
    return result, ctx
