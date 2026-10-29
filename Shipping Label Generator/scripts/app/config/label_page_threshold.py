from __future__ import annotations

from pathlib import Path

from shared.paths import shipping_config_workbook_path

# Fallback when the workbook sheet or cell A2 is missing or not a number.
DEFAULT_LABEL_PAGE_THRESHOLD = 10
_SHEET = "Label Page Threshold"


def read_label_page_threshold(path: Path | None = None) -> int:
    """Cell A2 on sheet Label Page Threshold. Bad or missing values fall back to 10."""
    book = path or shipping_config_workbook_path()
    if not book.is_file():
        return DEFAULT_LABEL_PAGE_THRESHOLD
    try:
        import openpyxl

        wb = openpyxl.load_workbook(book, read_only=True, data_only=True)
        try:
            if _SHEET not in wb.sheetnames:
                return DEFAULT_LABEL_PAGE_THRESHOLD
            raw = wb[_SHEET]["A2"].value
        finally:
            wb.close()
        n = int(raw)
    except Exception:
        return DEFAULT_LABEL_PAGE_THRESHOLD
    return n if n >= 1 else DEFAULT_LABEL_PAGE_THRESHOLD
