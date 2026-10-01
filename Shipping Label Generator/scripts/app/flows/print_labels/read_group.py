"""Read DTF Des CSV and group orders by process — stable façade."""

from __future__ import annotations

from app.flows.print_labels.read_group_build import read_and_group_orders
from app.flows.print_labels.read_group_types import GroupedOrders, OrderInput

__all__ = ["GroupedOrders", "OrderInput", "read_and_group_orders"]
