"""Process names with spaces (6-field sorter filenames) parse and format."""

from scripts.pipeline_generate_packing_list_pdf.core_helpers import (
    PROCESS_ITEM_RE,
    parse_process_and_item_impl,
    safe_str_impl,
)
from scripts.pipeline_split_by_process_item.grouping_assign import _sort_and_assign_merge_first
import pandas as pd


def test_parse_process_and_item_allows_spaces() -> None:
    pin = "Process 80-PRINTED-2-WAREHOUSE STOCK-P-S1-1-1 Item-2"
    proc, item = parse_process_and_item_impl(
        pin, safe_str=safe_str_impl, process_item_re=PROCESS_ITEM_RE
    )
    assert proc == "80-PRINTED-2-WAREHOUSE STOCK-P-S1-1-1"
    assert item == "2"


def test_simple_format_keeps_six_field_name() -> None:
    base = "PRINTED-2-SUPPLY ON DEMAND-R-S1-1"
    df = pd.DataFrame(
        [
            {
                "Process and Item Number": base,
                "Order Number": "ORD-1",
                "Gender Apparel": "Men",
                "Size": "S",
                "Colour": "Red",
                "Item Quantity": 1,
            },
            {
                "Process and Item Number": base,
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
        use_simple_process_format=True,
    )
    values = result["Process and Item Number"].tolist()
    assert values[0] == f"Process {base}-1 Item-1"
    assert values[1] == f"Process {base}-2 Item-1"


def test_excel_helpers_keep_warehouse_stock_spaces() -> None:
    from scripts.pipeline_generate_excel_outputs.helpers import (
        _extended_process_and_item_number,
        _item_number_from_extended,
        _process_plus_additional,
    )

    pin = "Process 80-PRINTED-2-WAREHOUSE STOCK-P-S1-1-1 Item-2"
    extended = _extended_process_and_item_number(pin)
    assert extended == "80-PRINTED-2-WAREHOUSE STOCK-P-S1-1-1-2"
    assert _process_plus_additional(extended) == "80-PRINTED-2-WAREHOUSE STOCK-P-S1-1-1"
    assert _item_number_from_extended(extended) == "2"
    assert _process_plus_additional("4200-1 1") == "4200-1"
    assert _item_number_from_extended("4200-1 1") == "1"
