"""ShipStation Tags.xlsx helpers (Process No + PDF name)."""
from __future__ import annotations

import os

from app_paths import shipstation_tags_path


def get_process_no_for_tag(tag_id: str):
    """Read Process No from ShipStation Tags.xlsx (C: Tag ID, D: Process No)."""
    try:
        try:
            import openpyxl
        except Exception:
            print("[WARNING] openpyxl not available to read ShipStation Tags.xlsx")
            return None

        xlsx_path = str(shipstation_tags_path())
        if not os.path.exists(xlsx_path):
            print(f"[WARNING] ShipStation Tags.xlsx not found at: {xlsx_path}")
            return None

        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active

        search_value = str(tag_id).strip()
        for row in ws.iter_rows(min_row=1):
            tag_cell = row[2]  # Column C (0-based index 2)
            process_cell = row[3]  # Column D (0-based index 3)
            tag_val = "" if tag_cell.value is None else str(tag_cell.value).strip()
            if tag_val == search_value:
                process_val = None if process_cell.value is None else str(process_cell.value).strip()
                return process_val or None
        return None
    except Exception as e:
        print(f"[WARNING] Failed to read Process No from ShipStation Tags.xlsx: {e}")
        return None


def pdf_filename_for_tag(tag_id: str, process_no: str | None = None) -> str:
    if process_no is None:
        process_no = get_process_no_for_tag(tag_id)
    if process_no:
        return f"{process_no}.pdf"
    return f"Tag_{tag_id}.pdf"
