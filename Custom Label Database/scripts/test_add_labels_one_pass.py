"""One-pass peers must match two-pass peers. Uses a tiny fixture CSV."""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from add_labels_peers import (
    _collect_peers_for_labels,
    _scan_existing,
    _scan_existing_and_peers,
)


def main() -> None:
    fields = ["Custom Label", "Gender Apparel", "Colour", "Size"]
    rows = [
        {"Custom Label": "W101-SkyBe-O/S-Yes", "Gender Apparel": "Other", "Colour": "Sky", "Size": "O/S"},
        {"Custom Label": "W101-SkyBe-O/S-Yes", "Gender Apparel": "FOTL Tee", "Colour": "Sky", "Size": "O/S"},
        {"Custom Label": "W101-Red-O/S-Yes", "Gender Apparel": "FOTL Tee", "Colour": "Red", "Size": "O/S"},
        {"Custom Label": "Other-Label", "Gender Apparel": "x", "Colour": "x", "Size": "x"},
    ]
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "cl.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        labels = ["W101-SkyBe-XL-Yes"]
        fieldnames, existing, peers = _scan_existing_and_peers(path, labels)
        field2, existing2 = _scan_existing(path)
        peers2 = _collect_peers_for_labels(path, field2, labels)
        assert fieldnames == field2 == fields
        assert existing == existing2
        assert peers == peers2
        assert peers["w101-skybe-o/s-yes"]["Gender Apparel"].startswith("FOTL")
    print("ok")


if __name__ == "__main__":
    main()
