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
def _is_test_mode() -> bool:
    """
    Guardrail to prevent mock/test data leaking into production runs.

    Enable by setting SHIPPING_TEST_MODE=1 (or true/yes/on).
    """
    v = (os.getenv("SHIPPING_TEST_MODE") or "").strip().lower()
    return v in ("1", "true", "yes", "y", "on")
class OrderResult:
    order_number: str
    process_number: str
    label_pdf_path: Path
    failure: FailureRow | None
    ship_from: str | None = None
