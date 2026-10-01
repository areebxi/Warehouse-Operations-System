from datetime import date
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from .helpers import _extended_process_and_item_number, _gender_colour_size_combo_hyphenated, _item_number_from_extended, _normalize, _order_number_base, _process_number_for_excel_from_row, _process_plus_additional, _remap_dtf_item_sku, _split_item_sku_by_lg
def _write_picking(df: pd.DataFrame, process_base: str, picking_number: str, dispatch_date: date, path: Path) -> None:
    rows_out = []
    for _, row in df.iterrows():
        qty = int(row.get("Item Quantity", 1) or 1)
        if qty < 1:
            qty = 1
        process_and_item = row.get("Process and Item Number", "")
        extended = _extended_process_and_item_number(process_and_item)
        process_excel = _process_number_for_excel_from_row(process_and_item)
        item_num = _item_number_from_extended(extended)
        for i in range(qty):
            bulk = qty - i
            rows_out.append({
                "dispatch_date": dispatch_date,
                "Picking Number": picking_number if not rows_out else "",
                "Process Number": process_excel,
                "Item Number": item_num,
                "Custom Label": _normalize(row.get("Item SKU", "")),
                "Gender-Apparel": _normalize(row.get("Gender Apparel", "")),
                "Color": _normalize(row.get("Colour", "")),
                "Size": _normalize(row.get("Size", "")),
                "Qty": qty,
                "Bulk": bulk,
                "Missing Apparel": "",
                "Status": "",
                "Order Number": _order_number_base(row),
            })
    if not rows_out:
        wb = Workbook()
        ws = wb.active
        ws.title = "Picking"
        ws.cell(row=1, column=1, value="Date")
        wb.save(path)
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Picking"
    ws.cell(row=1, column=1, value="Date")
    ws.cell(row=1, column=2, value="Picking Number")
    ws.cell(row=1, column=3, value="Process Number")
    ws.cell(row=1, column=4, value="Item Number")
    ws.cell(row=1, column=5, value="Custom Label")
    ws.cell(row=1, column=6, value="Gender-Apparel")
    ws.cell(row=1, column=7, value="Color")
    ws.cell(row=1, column=8, value="Size")
    ws.cell(row=1, column=9, value="Qty")
    ws.cell(row=1, column=10, value="Bulk")
    ws.cell(row=1, column=11, value="Missing Apparel")
    ws.cell(row=1, column=12, value="Status")
    ws.cell(row=1, column=27, value="Order Number (Base)")
    ws.cell(row=1, column=28, value="Process Number")
    ws.cell(row=1, column=29, value="Item Number")
    ws.cell(row=1, column=53, value="Process Number")
    ws.cell(row=1, column=54, value="Item Number")
    ws.cell(row=1, column=55, value="Picking Number")
    ws.cell(row=1, column=56, value="Gender-Apparel")
    ws.cell(row=1, column=57, value="Color")
    ws.cell(row=1, column=58, value="Size")
    ws.cell(row=1, column=59, value="Bulk")
    ws.cell(row=1, column=60, value="Missing Apparel")
    ws.cell(row=1, column=61, value="Status")

    date_str = dispatch_date.strftime("%d-%m-%Y")
    for r, d in enumerate(rows_out, start=2):
        pref_process = f"Process {d['Process Number']}" if d["Process Number"] else ""
        pref_item = f"Item-{d['Item Number']}" if d["Item Number"] else ""
        ws.cell(row=r, column=1, value=date_str)
        ws.cell(row=r, column=2, value=d["Picking Number"])
        ws.cell(row=r, column=3, value=d["Process Number"])
        ws.cell(row=r, column=4, value=d["Item Number"])
        ws.cell(row=r, column=5, value=d["Custom Label"])
        ws.cell(row=r, column=6, value=d["Gender-Apparel"])
        ws.cell(row=r, column=7, value=d["Color"])
        ws.cell(row=r, column=8, value=d["Size"])
        ws.cell(row=r, column=9, value=d["Qty"])
        ws.cell(row=r, column=10, value=d["Bulk"])
        ws.cell(row=r, column=11, value=d["Missing Apparel"])
        ws.cell(row=r, column=12, value=d["Status"])
        ws.cell(row=r, column=27, value=d["Order Number"])
        ws.cell(row=r, column=28, value=pref_process)
        ws.cell(row=r, column=29, value=pref_item)
        ws.cell(row=r, column=53, value=d["Process Number"])
        ws.cell(row=r, column=54, value=d["Item Number"])
        ws.cell(row=r, column=55, value=d["Picking Number"])
        ws.cell(row=r, column=56, value=d["Gender-Apparel"])
        ws.cell(row=r, column=57, value=d["Color"])
        ws.cell(row=r, column=58, value=d["Size"])
        ws.cell(row=r, column=59, value=d["Bulk"])
        ws.cell(row=r, column=60, value=d["Missing Apparel"])
        ws.cell(row=r, column=61, value=d["Status"])

    wb.save(path)
