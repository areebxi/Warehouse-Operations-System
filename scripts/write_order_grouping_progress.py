"""Regenerate order-grouping-progress.xlsx from order-grouping-locks.md — façade."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from write_order_grouping_progress_board import sheet_board
from write_order_grouping_progress_sheets import sheet_catalog, sheet_design


def main() -> int:
    from openpyxl import Workbook

    out = ROOT / "order-grouping-progress.xlsx"
    wb = Workbook()
    sheet_board(wb)
    sheet_catalog(wb)
    sheet_design(wb)
    wb.save(out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
