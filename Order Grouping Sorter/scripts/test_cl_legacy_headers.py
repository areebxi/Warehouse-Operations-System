"""Areeb spaced Custom Label header still indexes for grouping."""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from catalogs import load_cl_index  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cl.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["Custom Label", "Supply Method", "Gender Apparel"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "Custom Label": "M-T-BLK-M",
                    "Supply Method": "Warehouse Stock",
                    "Gender Apparel": "Mens-T-Shirt",
                }
            )
        index = load_cl_index(path)
    row = index["m-t-blk-m"]
    assert row["Custom_Label"] == "M-T-BLK-M"
    assert row["Stock_Type"] == "Warehouse Stock"
    assert row["Gender_Apparel"] == "Mens-T-Shirt"
    print("ok")


if __name__ == "__main__":
    main()
