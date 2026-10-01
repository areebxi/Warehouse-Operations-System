from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger


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

def _audit_fail(
    audit: OrderAuditLogger | None,
    *,
    order_number: str,
    process_number: str,
    customer_name: str,
    reason: str,
    shipstation_order_id: str = "",
    **fields: Any,
) -> None:
    if audit is None:
        return
    audit.record(
        outcome="print_failed",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        reason=reason,
        shipstation_order_id=shipstation_order_id,
        **fields,
    )

