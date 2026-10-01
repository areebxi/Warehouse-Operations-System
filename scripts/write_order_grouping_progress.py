"""Regenerate order-grouping-progress.xlsx from order-grouping-locks.md — façade."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from write_order_grouping_progress_board import sheet_board
from write_order_grouping_progress_sheets import sheet_catalog, sheet_design
from write_order_grouping_progress_style import f, put, widths


def main() -> int:
    from openpyxl import Workbook

    out = ROOT / "order-grouping-progress.xlsx"
    wb = Workbook()
    sheet_board(wb.active)
    sheet_catalog(wb.create_sheet("Catalog joins"))
    sheet_design(wb.create_sheet("Design notes"))
    for ws in wb.worksheets:
        widths(ws)
    wb.save(out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
