"""process_one_order orchestrator — selection/label steps live in sibling modules."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from app.config.load import AppConfig
from app.flows.print_labels.failures import FailureRow
from app.flows.print_labels.order_audit import _audit_fail
from app.flows.print_labels.order_result import OrderResult, ServiceCodeResolutionError
from app.flows.print_labels.process_order_label import create_or_reuse_label
from app.flows.print_labels.process_order_select import select_order_for_print
from app.logging.jsonl import JsonlLogger
from app.providers.base import Provider

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger


async def process_one_order(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name_from_input: str = "",
    labels_dir: Path,
    audit: OrderAuditLogger | None = None,
) -> OrderResult:
    customer_name_from_input = str(customer_name_from_input or "")
    customer_name: str = customer_name_from_input
    from app.pdf.report_pages import make_label_error_page_pdf

    def _write_error_pdf(*, reason: str, customer: str) -> Path:
        labels_dir.mkdir(parents=True, exist_ok=True)
        out_path = labels_dir / f"{order_number}__ERROR.pdf"
        out_path.write_bytes(
            make_label_error_page_pdf(
                process_number=process_number,
                order_number=order_number,
                customer_name=customer,
                error_reason=reason,
            )
        )
        return out_path

    if audit is not None:
        audit.record(
            outcome="print_start",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name_from_input,
        )

    selected = None
    shipment_fields: dict[str, Any] = {}
    carrier = service = package = ""
    try:
        selected, customer_name, early = await select_order_for_print(
            cfg=cfg,
            log=log,
            provider=provider,
            process_number=process_number,
            order_number=order_number,
            customer_name_from_input=customer_name_from_input,
            customer_name=customer_name,
            audit=audit,
            write_error_pdf=_write_error_pdf,
        )
        if early is not None:
            return early
        assert selected is not None
        result, ctx = await create_or_reuse_label(
            cfg=cfg,
            log=log,
            provider=provider,
            process_number=process_number,
            order_number=order_number,
            customer_name=customer_name,
            selected=selected,
            labels_dir=labels_dir,
            audit=audit,
        )
        selected = ctx.get("selected", selected)
        shipment_fields = ctx.get("shipment_fields") or {}
        carrier = ctx.get("carrier") or ""
        service = ctx.get("service") or ""
        package = ctx.get("package") or ""
        return result

    except ServiceCodeResolutionError as e:
        log.error(
            "print_order_failed",
            extra={"order_number": order_number, "process_number": process_number},
            exc=e,
        )
        reason = str(e)
        if customer_name_from_input:
            customer_name = customer_name_from_input
        order_id = str(getattr(selected, "orderId", "") or "") if selected is not None else ""
        if selected is not None:
            customer_name = customer_name or str(getattr(selected, "customerName", "") or "")
        package_code = str(shipment_fields.get("packageCode") or "") if isinstance(shipment_fields, dict) else ""
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            reason=reason,
            shipstation_order_id=order_id,
            carrier_code=e.carrier_code or "",
            service_code=e.order_service_code or e.shipment_service_code or "",
            package_code=package_code,
            requested_shipping_service=e.requested_shipping_service or "",
            carrier_key=e.carrier_key or "",
        )
        return OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=_write_error_pdf(reason=reason, customer=customer_name),
            failure=FailureRow(customer_name, process_number, order_number, order_id, reason),
            ship_from=None,
        )
    except Exception as e:
        log.error(
            "print_order_failed",
            extra={"order_number": order_number, "process_number": process_number},
            exc=e,
        )
        reason = str(e)
        if customer_name_from_input:
            customer_name = customer_name_from_input
        order_id = str(getattr(selected, "orderId", "") or "") if selected is not None else ""
        fail_fields: dict[str, Any] = {}
        if carrier:
            fail_fields["carrier_code"] = carrier
        if service:
            fail_fields["service_code"] = service
        if package:
            fail_fields["package_code"] = package
        if selected is not None:
            fail_fields["requested_shipping_service"] = selected.requestedShippingService or ""
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            reason=reason,
            shipstation_order_id=order_id,
            **fail_fields,
        )
        return OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=_write_error_pdf(reason=reason, customer=customer_name),
            failure=FailureRow(customer_name, process_number, order_number, order_id, reason),
            ship_from=None,
        )
