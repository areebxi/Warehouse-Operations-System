from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import pandas as pd

class GroupedOrders:
    process_number: str
    orders: list[OrderInput]
    source_file: str = ""
    source_index: int = 0

    @property
    def order_numbers(self) -> list[str]:
        return [o.order_number for o in self.orders]
class OrderInput:
    order_number: str
    customer_name: str = ""
