from __future__ import annotations

from scripts.app.models.order import Order
from scripts.app.rules.order_status import cancelled_order_reason, is_order_cancelled
from scripts.app.rules.selection import select_order_candidate


def test_is_order_cancelled() -> None:
    assert is_order_cancelled(Order(orderId=1, orderNumber="A", orderStatus="cancelled"))
    assert is_order_cancelled(Order(orderId=1, orderNumber="A", orderStatus="Cancelled"))
    assert is_order_cancelled(Order(orderId=1, orderNumber="A", orderStatus="canceled"))
    assert not is_order_cancelled(Order(orderId=1, orderNumber="A", orderStatus="awaiting_shipment"))
    assert not is_order_cancelled(Order(orderId=1, orderNumber="A", orderStatus=None))


def test_cancelled_order_reason() -> None:
    msg = cancelled_order_reason(
        orders=[Order(orderId=1, orderNumber="A", orderStatus="cancelled")],
    )
    assert msg == "order is cancelled on channel (orderStatus=cancelled)"


def test_select_order_candidate_skips_cancelled() -> None:
    cancelled = Order(orderId=1, orderNumber="A", orderStatus="cancelled")
    active = Order(orderId=2, orderNumber="A", orderStatus="awaiting_shipment")
    picked = select_order_candidate(candidates=[cancelled, active], has_active_shipments={1: False, 2: False})
    assert picked is not None
    assert picked.orderId == 2
