"""ponytail: PIN short form — fails if batch+shift strip or Item spacing drifts."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline_split_by_process_item.common import format_batch_pin, pin_batch_shift
from pipeline_generate_packing_list_pdf.core_helpers import (
    PROCESS_ITEM_RE,
    parse_process_and_item_impl,
    safe_str_impl,
)


def test_pin_batch_shift() -> None:
    assert pin_batch_shift("B100-S1-PRINTED-2-WAREHOUSE STOCK-R-1") == "B100-S1"
    assert pin_batch_shift("B1-S2-PRINTED-2-SUPPLY ON DEMAND-R-3") == "B1-S2"
    assert pin_batch_shift("B1-S1-PLAIN-2-SUPPLY ON DEMAND-R-9") == "B1-S1"
    assert pin_batch_shift("RESEND") == "RESEND"


def test_format_batch_pin() -> None:
    assert (
        format_batch_pin("B100-S1-PRINTED-2-WAREHOUSE STOCK-R-1", 1, 1)
        == "B100-S1-1 Item 1"
    )
    assert format_batch_pin("B1-S1-PLAIN-2-SUPPLY ON DEMAND-R-2", 2, 3) == "B1-S1-2 Item 3"


def test_parse_new_and_legacy_pin() -> None:
    def parse(v: str):
        return parse_process_and_item_impl(
            v, safe_str=safe_str_impl, process_item_re=PROCESS_ITEM_RE
        )

    assert parse("B100-S1-1 Item 1") == ("B100-S1-1", "1")
    assert parse("Process B100-S1-PRINTED-2-WAREHOUSE STOCK-R-1-1 Item-1") == (
        "B100-S1-PRINTED-2-WAREHOUSE STOCK-R-1-1",
        "1",
    )


if __name__ == "__main__":
    test_pin_batch_shift()
    test_format_batch_pin()
    test_parse_new_and_legacy_pin()
    print("ok")
