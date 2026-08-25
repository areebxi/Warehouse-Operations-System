"""Tests for Step 6 numeric process increment (10000, 10001 vs 10000-1)."""

import pandas as pd

from scripts.pipeline_split_by_process_item.common import (
    is_pure_numeric_process_base,
    _normalize_numeric_process_base,
)
from scripts.pipeline_split_by_process_item.grouping_assign import _sort_and_assign_merge_first


def test_is_pure_numeric_process_base():
    assert is_pure_numeric_process_base("10000")
    assert is_pure_numeric_process_base("100")
    assert is_pure_numeric_process_base("10000.0")
    assert not is_pure_numeric_process_base("49641LG")
    assert not is_pure_numeric_process_base("100A")
    assert not is_pure_numeric_process_base("200CNND1X")
    assert _normalize_numeric_process_base("10000.0") == "10000"


def test_numeric_base_increments_process_number():
    """Pure numeric base 10000 uses 10000, 10001 — not 10000-1, 10000-2."""
    df = pd.DataFrame(
        [
            {
                "Process and Item Number": "10000",
                "Order Number": "ORD-1",
                "Gender Apparel": "Men",
                "Size": "S",
                "Colour": "Red",
                "Item Quantity": 1,
            },
            {
                "Process and Item Number": "10000",
                "Order Number": "ORD-2",
                "Gender Apparel": "Women",
                "Size": "M",
                "Colour": "Blue",
                "Item Quantity": 1,
            },
        ]
    )
    result = _sort_and_assign_merge_first(
        df,
        size_to_rank=None,
        sequence_number=10005,
        use_simple_process_format=False,
        use_fixed_numeric_process=False,
    )
    values = result["Process and Item Number"].tolist()
    assert values == ["Process 10000 Item-1", "Process 10001 Item-1"]
    assert "10000-1" not in values[0]
    assert "10000-2" not in values[1]


def test_non_numeric_base_uses_dash_suffix_when_fixed_numeric_mode():
    """Alphanumeric bases keep dash format in fixed-numeric runs."""
    df = pd.DataFrame(
        [
            {
                "Process and Item Number": "49641LG",
                "Order Number": "ORD-1",
                "Gender Apparel": "Men",
                "Size": "S",
                "Colour": "Red",
                "Item Quantity": 1,
            },
            {
                "Process and Item Number": "49641LG",
                "Order Number": "ORD-2",
                "Gender Apparel": "Women",
                "Size": "M",
                "Colour": "Blue",
                "Item Quantity": 1,
            },
        ]
    )
    result = _sort_and_assign_merge_first(
        df,
        size_to_rank=None,
        sequence_number=10005,
        use_simple_process_format=False,
        use_fixed_numeric_process=True,
        fixed_process_number="100",
    )
    values = result["Process and Item Number"].tolist()
    assert values == ["Process 49641LG-1 Item-1", "Process 49641LG-2 Item-1"]
