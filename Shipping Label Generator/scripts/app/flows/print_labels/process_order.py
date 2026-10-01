"""Per-order print processing — stable façade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.flows.print_labels.process_order_impl1 import process_one_order
from app.flows.print_labels.process_order_impl2 import (
    ServiceCodeResolutionError,
    _audit_step,
    _extract_total_weight_lb,
    _resolve_fields,
    _timed_call_with_retries,
)
from app.flows.print_labels.process_order_impl3 import (
    OrderResult,
    _audit_fail,
    _is_test_mode,
    _pick_order_candidate_fast,
)

if TYPE_CHECKING:
    from app.logging.orders_audit import OrderAuditLogger

__all__ = [
    "OrderResult",
    "ServiceCodeResolutionError",
    "process_one_order",
]
