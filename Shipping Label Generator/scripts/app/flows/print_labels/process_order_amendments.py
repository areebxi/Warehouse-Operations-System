from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from app.flows.print_labels.failures import FailureRow
from app.flows.print_labels.order_audit import _audit_fail
from app.flows.print_labels.order_result import OrderResult
from app.logging.jsonl import JsonlLogger
from app.models.order import Order
from app.providers.base import Provider

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger


async def amendments_early_result(
    *,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name_from_input: str,
    customer_name: str,
    selected: Order,
    audit: OrderAuditLogger | None,
    write_error_pdf: Callable[..., Path],
) -> OrderResult | None:
    """Return an OrderResult if Amendments tag blocks printing; else None."""
    from app.flows.amendments.shipstation_tags import selected_order_has_amendments
    from app.flows.amendments.tags import amendments_skip_reason

    try:
        blocked, tag_info = await selected_order_has_amendments(
            provider,
            order_id=int(selected.orderId),
            order_number=order_number,
        )
    except Exception as e:
        log.warning(
            "print_amendments_check_failed",
            extra={
                "order_number": order_number,
                "process_number": process_number,
                "orderId": selected.orderId,
            },
            exc=e,
        )
        blocked, tag_info = False, None

    if not blocked:
        return None

    reason = amendments_skip_reason()
    cust = customer_name_from_input or customer_name or (tag_info.customer_name if tag_info else "")
    log.info(
        "print_skipped_amendments_tag",
        extra={
            "order_number": order_number,
            "process_number": process_number,
            "orderId": selected.orderId,
            "tag_names": list(tag_info.tag_names) if tag_info else [],
            "tag_count": int(tag_info.tag_count) if tag_info else 0,
        },
    )
    _audit_fail(
        audit,
        order_number=order_number,
        process_number=process_number,
        customer_name=cust,
        reason=reason,
        shipstation_order_id=str(selected.orderId),
        tag_names=list(tag_info.tag_names) if tag_info else [],
    )
    return OrderResult(
        order_number=order_number,
        process_number=process_number,
        label_pdf_path=write_error_pdf(reason=reason, customer=cust),
        failure=FailureRow(cust, process_number, order_number, str(selected.orderId), reason),
        ship_from=None,
    )
