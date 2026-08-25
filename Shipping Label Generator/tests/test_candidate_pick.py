from __future__ import annotations

from scripts.app.flows.print_labels.process_order import _pick_order_candidate_fast
from scripts.app.models.order import Order


def test_pick_order_candidate_fast_single_candidate_returns_it_without_checks() -> None:
    c = Order(orderId=1, orderNumber="A1")
    assert _pick_order_candidate_fast(candidates=[c], has_active_shipments={}) == c


def test_pick_order_candidate_fast_single_cancelled_returns_none() -> None:
    c = Order(orderId=1, orderNumber="A1", orderStatus="cancelled")
    assert _pick_order_candidate_fast(candidates=[c], has_active_shipments={}) is None


def test_pick_order_candidate_fast_multiple_candidates_preserves_existing_rules() -> None:
    # Existing rules prefer candidates with no active shipments, highest orderId.
    c1 = Order(orderId=1, orderNumber="A1")
    c2 = Order(orderId=2, orderNumber="A1")
    picked = _pick_order_candidate_fast(candidates=[c1, c2], has_active_shipments={1: True, 2: False})
    assert picked == c2

