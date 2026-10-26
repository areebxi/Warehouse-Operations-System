"""Order-number read + rate-limit pause. No network."""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from tag_shift_orders import order_numbers, tag_id_for
from tag_shift_workers import pause_seconds


def main() -> None:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "batch.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["Order #", "Item SKU"])
            writer.writeheader()
            writer.writerow({"Order #": "A1", "Item SKU": "x"})
            writer.writerow({"Order #": "A1", "Item SKU": "y"})
            writer.writerow({"Order #": " B2 ", "Item SKU": "z"})
        assert order_numbers([path]) == ["A1", "B2"]
    name, tag_id = tag_id_for([{"name": "001-1st Shift", "tagId": 30020}], "1st")
    assert name == "001-1st Shift" and tag_id == 30020
    assert pause_seconds({"X-Rate-Limit-Remaining": "20"}) == 0.0
    assert pause_seconds({"X-Rate-Limit-Remaining": "1", "X-Rate-Limit-Reset": "3"}) == 3.0
    assert pause_seconds({"X-Rate-Limit-Remaining": "8", "X-Rate-Limit-Reset": "2"}, floor=8) == 2.0
    assert pause_seconds({"X-Rate-Limit-Remaining": "9"}, floor=8) == 0.0
    print("ok")


if __name__ == "__main__":
    main()
