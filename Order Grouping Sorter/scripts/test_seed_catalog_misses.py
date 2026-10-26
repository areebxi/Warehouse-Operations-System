"""catalog_miss_skus helper. No network."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from grouping_models import LineAttrs, Order
from seed_catalog_misses import catalog_miss_skus


def _line(sku: str, finish: str | None) -> LineAttrs:
    return LineAttrs(sku=sku, qty=1, finish=finish, source=None)


def main() -> None:
    orders = [
        Order(
            number="1",
            ship_by_raw="",
            ship_by=None,
            tag_names=[],
            store_name="",
            lines=[
                _line("A-MISS-1", None),
                _line("B-HIT", "printed"),
                _line("a-miss-1", None),
                _line("", None),
            ],
        ),
        Order(
            number="2",
            ship_by_raw="",
            ship_by=None,
            tag_names=[],
            store_name="",
            lines=[_line("C-MISS-2", None)],
        ),
    ]
    assert catalog_miss_skus(orders) == ["A-MISS-1", "C-MISS-2"]
    print("ok")


if __name__ == "__main__":
    main()
