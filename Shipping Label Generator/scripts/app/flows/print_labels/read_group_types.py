"""Order grouping types for print-label CSV ingest."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OrderInput:
    order_number: str
    customer_name: str = ""


@dataclass
class GroupedOrders:
    process_number: str
    orders: list[OrderInput]
    source_file: str = ""
    source_index: int = 0

    @property
    def order_numbers(self) -> list[str]:
        return [o.order_number for o in self.orders]
