from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from app.config.load import AppConfig
from app.flows.print_labels.failures import FailureRow
from app.flows.print_labels.order_audit import _audit_fail, _audit_step
from app.flows.print_labels.order_fields import _pick_order_candidate_fast
from app.flows.print_labels.order_result import OrderResult
from app.flows.print_labels.order_retries import _timed_call_with_retries
from app.flows.print_labels.process_order_amendments import amendments_early_result
from app.logging.jsonl import JsonlLogger
from app.models.order import Order
from app.providers.base import Provider
from app.rules.order_status import cancelled_order_reason, is_order_cancelled

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger


async def select_order_for_print(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name_from_input: str,
    customer_name: str,
    audit: OrderAuditLogger | None,
    write_error_pdf: Callable[..., Path],
) -> tuple[Order | None, str, OrderResult | None]:
    """
    Lookup / cancel / pick / amendments gate.

    Returns (selected, customer_name, early_result).
    If early_result is set, caller should return it immediately.
    """
    candidates = await _timed_call_with_retries(
        cfg=cfg,
        log=log,
        op="lookup_orders",
        op_kind="request",
        fn=lambda: provider.lookup_orders(order_number),
        extra={"order_number": order_number, "process_number": process_number},
    )
    _audit_step(
        audit,
        outcome="print_lookup",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        candidate_count=int(len(candidates)),
    )
    if not candidates:
        reason = "order not found"
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            reason=reason,
        )
        return None, customer_name, OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=write_error_pdf(reason=reason, customer=customer_name),
            failure=FailureRow(customer_name, process_number, order_number, "", reason),
            ship_from=None,
        )

    if all(is_order_cancelled(o) for o in candidates):
        reason = cancelled_order_reason(orders=candidates)
        cust = customer_name_from_input or (candidates[0].customerName or "")
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=cust,
            reason=reason,
            shipstation_order_id=str(candidates[0].orderId),
        )
        return None, cust, OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=write_error_pdf(reason=reason, customer=cust),
            failure=FailureRow(
                cust,
                process_number,
                order_number,
                str(candidates[0].orderId),
                reason,
            ),
            ship_from=None,
        )

    shippable_candidates = [o for o in candidates if not is_order_cancelled(o)]

    has_active: dict[int, bool] = {}
    if len(shippable_candidates) > 1:
        for o in shippable_candidates:
            sh = await _timed_call_with_retries(
                cfg=cfg,
                log=log,
                op="list_shipments",
                op_kind="request",
                fn=lambda o=o: provider.list_shipments(o.orderId, include_voided=False, page_size=1),
                extra={
                    "order_number": order_number,
                    "process_number": process_number,
                    "orderId": o.orderId,
                    "include_voided": False,
                },
            )
            has_active[o.orderId] = len(sh) > 0

    selected = _pick_order_candidate_fast(candidates=shippable_candidates, has_active_shipments=has_active)
    if selected is None:
        reason = "no processable order candidate (all have active shipments)"
        cust = customer_name_from_input or (candidates[0].customerName or "")
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=cust,
            reason=reason,
            shipstation_order_id=str(candidates[0].orderId),
        )
        return None, cust, OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=write_error_pdf(reason=reason, customer=cust),
            failure=FailureRow(
                cust,
                process_number,
                order_number,
                str(candidates[0].orderId),
                reason,
            ),
            ship_from=None,
        )

    customer_name = selected.customerName or customer_name or ""
    _audit_step(
        audit,
        outcome="print_order_selected",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        shipstation_order_id=str(selected.orderId),
        requested_shipping_service=selected.requestedShippingService or "",
        candidate_count=int(len(candidates)),
        shippable_candidate_count=int(len(shippable_candidates)),
    )

    early_amend = await amendments_early_result(
        log=log,
        provider=provider,
        process_number=process_number,
        order_number=order_number,
        customer_name_from_input=customer_name_from_input,
        customer_name=customer_name,
        selected=selected,
        audit=audit,
        write_error_pdf=write_error_pdf,
    )
    if early_amend is not None:
        cust = early_amend.failure.customer_name if early_amend.failure else customer_name
        return None, cust, early_amend

    return selected, customer_name, None
