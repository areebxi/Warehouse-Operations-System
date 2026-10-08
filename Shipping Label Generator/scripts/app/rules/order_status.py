from __future__ import annotations

from scripts.app.models.order import Order

_CANCELLED_STATUSES = frozenset({"cancelled", "canceled"})


def is_order_cancelled(order: Order) -> bool:
    status = (order.orderStatus or "").strip().lower().replace(" ", "_")
    return status in _CANCELLED_STATUSES


def cancelled_order_reason(*, orders: list[Order]) -> str:
    statuses = sorted({(o.orderStatus or "unknown").strip() for o in orders if (o.orderStatus or "").strip()})
    status_text = statuses[0] if len(statuses) == 1 else ", ".join(statuses)
    return f"order is cancelled on channel (orderStatus={status_text})"
