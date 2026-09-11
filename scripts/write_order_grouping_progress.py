"""Simple CEO progress workbook. Re-run after locks change."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.worksheet import Worksheet

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "order-grouping-progress.xlsx"

NAVY = "1F4E79"
WHITE = "FFFFFF"
GREEN = "C6EFCE"
GREEN_F = "006100"
YELLOW = "FFF2CC"
YELLOW_F = "7F6000"
ORANGE = "FCE4D6"
ORANGE_F = "C65911"
BLUE = "DDEBF7"
GREY = "F2F2F2"
LINE = Border(
    left=Side(style="thin", color="BDD7EE"),
    right=Side(style="thin", color="BDD7EE"),
    top=Side(style="thin", color="BDD7EE"),
    bottom=Side(style="thin", color="BDD7EE"),
)
C = Alignment(wrap_text=True, vertical="center", horizontal="center")
L = Alignment(wrap_text=True, vertical="center", horizontal="left")


def f(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def put(ws, r, c, val, *, bg=None, fg="000000", bold=False, size=11, align=L):
    cell = ws.cell(r, c, val)
    cell.font = Font(name="Calibri", bold=bold, color=fg, size=size)
    cell.alignment = align
    cell.border = LINE
    if bg:
        cell.fill = f(bg)
    return cell


def widths(ws: Worksheet, d: dict[str, float]) -> None:
    for k, v in d.items():
        ws.column_dimensions[k].width = v


def sheet_board(wb: Workbook) -> None:
    ws = wb.active
    ws.title = "Board"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_view.showGridLines = False
    ws.row_dimensions[1].height = 26
    put(ws, 1, 1, "Order grouping  ·  " + date.today().isoformat(), bg=NAVY, fg=WHITE, bold=True, size=16, align=L)
    ws.merge_cells("A1:L1")
    put(ws, 2, 1, "Green = locked     Yellow = off (v1)     Graph values = examples     1 logic ✓  2 catalog fill ✓  3 Order Grouping Sorter  4 dry-run (no Input write until run)", bg=BLUE, bold=True, align=L)
    ws.merge_cells("A2:L2")

    # Process name
    put(ws, 4, 1, "Process name", bg=NAVY, fg=WHITE, bold=True, align=C)
    slots = [
        ("today", GREEN, "or YYYY-MM-DD if future-fill"),
        ("1st", GREEN, "2nd / 3rd — also the Input folder"),
        ("plain", GREEN, "SKU plain/plainlg OR Plain Database/Packs match"),
        ("own", GREEN, "or peeled channel e.g. fawad"),
        ("x", YELLOW, "design groups off"),
        ("prime", GREEN, "tag Amazon Prime Order"),
        ("dtf", GREEN, "printed only; CL Printing Type"),
        ("readymade", GREEN, "printed only; Customise"),
        ("x", YELLOW, "custom type off"),
    ]
    for i, (name, bg, meaning) in enumerate(slots):
        col = 2 + i
        put(ws, 4, col, name, bg=bg, bold=True, size=12, align=C)
        put(ws, 5, col, meaning, bg=GREY, size=9, align=C)
    put(ws, 5, 1, "printed ex.", bg=GREY, size=9, align=C)
    ws.row_dimensions[5].height = 36

    put(ws, 6, 1, "plain name", bg=GREY, size=9, align=C)
    put(ws, 6, 2, "Shift is the Input folder (1st Shift / 2nd Shift / 3rd Shift) and a filename slot (1st / 2nd / 3rd). Plain skips dtf / readymade / package-type (slots x). Adds supply-method and supplier when flags are 1. Packs vs Gildan = 30-chain (no pack colour). Amazon stays in own. MAS Clothing → fawad.", bg=GREEN, fg=GREEN_F, size=9, align=L)
    ws.merge_cells("B6:J6")

    put(ws, 8, 1, "resend", bg=YELLOW, fg=YELLOW_F, bold=True, align=C)
    put(ws, 8, 2, "filename is only:  resend     Exact tag 1014-ALL-RESEND only (not 1015 / 1016 / 1017). Wins even if ship-by is blank.", bg=YELLOW, align=L)
    ws.merge_cells("B8:J8")
    put(ws, 9, 1, "unmatched", bg=ORANGE, fg=ORANGE_F, bold=True, align=C)
    put(ws, 9, 2, "filename is only:  unmatched     No definite match. Floor handles this run; then investigate and tighten so the next run matches. Same order stays together.", bg=ORANGE, align=L)
    ws.merge_cells("B9:J9")

    put(ws, 11, 1, "This shift", bg=NAVY, fg=WHITE, bold=True, align=C)
    ws.merge_cells("A11:F11")
    intake = [
        "1. ShipStation\nawaiting_shipment only",
        "2. Skip\npost-order-designs",
        "3. Resend tag?\n→ file “resend”",
        "4. Blank ship-by\n→ unmatched",
        "5. Today/overdue first\nthen future to fill cap",
        "6. Folders 1st/2nd/3rd\n300/100/100 LINES",
    ]
    for i, t in enumerate(intake):
        put(ws, 12, 1 + i, t, bg=GREEN, fg=GREEN_F, bold=True, size=10, align=C)
        ws.merge_cells(start_row=12, start_column=1 + i, end_row=13, end_column=1 + i)
    ws.row_dimensions[12].height = 22
    ws.row_dimensions[13].height = 28

    # Splits
    put(ws, 15, 1, "New process file when flag is 1", bg=NAVY, fg=WHITE, bold=True, align=L)
    ws.merge_cells("A15:J15")
    headers = ["Split", "Plain", "Printed", "Where", "v1"]
    for i, h in enumerate(headers):
        put(ws, 16, 1 + i, h, bg=NAVY, fg=WHITE, bold=True, align=C)
    splits = [
        ("shift", "on", "on", "Filename slot 1st / 2nd / 3rd after today or YYYY-MM-DD. Also the Input folder (1st Shift = 300 lines, 2nd = 100, 3rd = 100)", "on"),
        ("plain / printed", "on", "on", "Finish gate: SKU plain/plainlg → plain; else CL hit (after 1st dash) → printed; else Plain Database till-last-dash or Packs whole → plain; else unmatched", "on"),
        ("store / channel", "on", "on", "MAS Clothing → process name fawad; more later; Amazon stays in own", "on"),
        ("design group", "off", "off", "per scenario, Design ID lists", "off"),
        ("prime", "on", "on", "tag Amazon Prime Order (not CL Amazon Prime)", "on"),
        ("printing method", "off", "on", "CL Printing Type — DTF default; Sublimation = mugs", "on"),
        ("ready-made / customised", "off", "on", "CL Customise", "on"),
        ("customisation type", "off", "off", "CL Customisation Type (column empty; v1 slot x)", "off"),
        ("print size", "off", "off", "CL Print Size 1", "off"),
        ("print position", "off", "off", "CL Print Positions", "off"),
        ("supply method", "on", "on", "Warehouse Stock = FOTL men/women/kids t-shirts only. In House Manufacture = SKU/GA contains iron on / ironon / iron-on / sticker (printed). Supplier On Demand = Gildan tees + everything else. Plain never in-house.", "on"),
        ("supplier", "on", "stock off / on-demand on", "Supplier Name: BTC Activewear / Uneek Clothing / Absolute Apparels (babysuits C800T C8020T C8030T only)", "on"),
        ("package type", "off", "off", "packing PDF only (Large Letter / Parcel). Packs vs Gildan = 30-chain", "off"),
    ]

    def flag_bg(v: str) -> str:
        if v == "on":
            return GREEN
        if v == "off":
            return YELLOW
        if v.startswith("on"):
            return ORANGE
        return GREY

    for r, row in enumerate(splits, start=17):
        put(ws, r, 1, row[0], bold=True, align=L)
        put(ws, r, 2, row[1], bg=flag_bg(row[1]), align=C)
        put(ws, r, 3, row[2], bg=flag_bg(row[2]), align=C)
        put(ws, r, 4, row[3], align=L)
        put(ws, r, 5, row[4], bg=flag_bg(row[4]), bold=True, align=C)
    put(ws, 30, 1, "Order Grouping Sorter (new app) writes Packing Input/{DD-MM-YYYY}/{1st|2nd|3rd} Shift/. Dry-run first: counts + process names, no Input write until run. Packs colour later.", bg=GREEN, fg=GREEN_F, align=L)
    ws.merge_cells("A30:E30")

    # 30 chain
    put(ws, 32, 1, "Then, if a bucket has 30+ units → another process file", bg=NAVY, fg=WHITE, bold=True, align=L)
    ws.merge_cells("A32:I32")
    chain = [
        ("Category (Areeb)", GREEN, "filled"),
        ("Product Type (Areeb)", GREEN, "filled"),
        ("Product Style (Areeb)", GREEN, "filled"),
        ("Department (Areeb)", GREEN, "filled"),
        ("Brand / Brand Name", GREEN, "have"),
        ("Size / Pack Size", GREEN, "have"),
        ("Colour", GREEN, "have; packs later"),
    ]
    for i, (name, bg, note) in enumerate(chain):
        put(ws, 33, 1 + i, name, bg=bg, bold=True, align=C)
        put(ws, 34, 1 + i, note, bg=bg, size=9, align=C)

    put(ws, 35, 1, "Plain: every step 30     Printed: department always on, brand off, size on, colour 30", bg=GREY, size=10, align=L)
    ws.merge_cells("A35:I35")

    put(ws, 36, 1, "If a branch is not drawn all the way to colour, it still uses this chain (blank = save writing, not skip).", bg=YELLOW, fg=YELLOW_F, bold=True, align=L)
    ws.merge_cells("A36:I36")
    put(ws, 37, 1, "Printed in-house (iron-on or sticker, made here) uses the same 30-chain tail as warehouse-stock. Plain cannot be in-house. Mixed plain+printed order → whole order printed.", bg=YELLOW, align=L)
    ws.merge_cells("A37:I37")

    put(ws, 39, 1, "On each packing line", bg=NAVY, fg=WHITE, bold=True, align=L)
    ws.merge_cells("A39:J39")
    put(ws, 40, 1, "Process today-1st-plain-own-…-1 Item 1     then     …-1 Item 2     then     …-2 Item 1", bg=GREEN, fg=GREEN_F, bold=True, align=C)
    ws.merge_cells("A40:J40")
    put(ws, 41, 1, "-1 / -2 = colour groups (3+ qty) first, then parts of 50 units. Item 1, 2 = lines. Same order keeps the same -N. Packs skip colour groups.", bg=GREY, align=L)
    ws.merge_cells("A41:J41")

    widths(ws, {**{chr(65 + i): 16 for i in range(12)}, "A": 26, "B": 18, "C": 28, "D": 42, "E": 22})
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 44
    ws.column_dimensions["E"].width = 18
    for col in "FGHIJ":
        ws.column_dimensions[col].width = 16
    ws.freeze_panes = "A3"
    ws.print_area = "A1:J41"
    ws.page_setup.horizontalCentered = True
    ws.oddHeader.left.text = "Order grouping progress"


def sheet_catalog(wb: Workbook) -> None:
    ws = wb.create_sheet("Catalog")
    ws.page_setup.orientation = "landscape"
    ws.sheet_view.showGridLines = False
    put(ws, 1, 1, "Step 2 — catalog fill done (2026-09-08/09). Sorter reads; it does not overwrite.", bg=NAVY, fg=WHITE, bold=True, size=16, align=L)
    ws.merge_cells("A1:D1")
    put(ws, 2, 1, "30-chain = Areeb columns. Do not overwrite PE Department. Packs colour later. Backup before any future fill.", bg=YELLOW, fg=YELLOW_F, bold=True, align=L)
    ws.merge_cells("A2:D2")
    for i, h in enumerate(["Column", "Do this", "Used for", "v1"]):
        put(ws, 4, 1 + i, h, bg=NAVY, fg=WHITE, bold=True, align=C)
    rows = [
        ("Customise (CL)", "have (Yes / blank)", "ready-made vs customised", GREEN, "on"),
        ("Printing Type (CL)", "FILLED — DTF / mug Sublimation", "printed printing method", GREEN, "on"),
        ("Supply Method (all 3)", "FILLED — FOTL tees / iron-on+sticker / on-demand", "Warehouse Stock, In House Manufacture, Supplier On Demand", GREEN, "on"),
        ("Package Type / Package", "CL 34%; Plain 100%; display", "packing PDF; grouping off", YELLOW, "off"),
        ("Supplier Name", "FILLED — BTC Activewear / Uneek Clothing / Absolute babysuits", "supplier split when flag 1", GREEN, "on"),
        ("Category (Areeb)", "FILLED on all 3", "≥30 new file", GREEN, "on"),
        ("Product Type (Areeb)", "FILLED on all 3", "≥30 new file", GREEN, "on"),
        ("Product Style (Areeb)", "FILLED on all 3", "≥30 new file", GREEN, "on"),
        ("Department (Areeb)", "FILLED; CL = gender only", "plain 30 / printed 1", GREEN, "on"),
        ("Brand, Size, Colour", "have (Packs: Brand Name + Pack Size; colour later)", "30+ files; colour 3+ qty → -N (not packs)", GREEN, "on"),
        ("Print Size 1", "leave; fill later", "print size split (v2)", YELLOW, "off"),
        ("Print Positions", "have; split later", "print position split (v2)", YELLOW, "off"),
        ("Amazon Prime (CL)", "leave — not grouping", "PO / inventory only", YELLOW, "not grouping"),
        ("customisation type", "CL column empty; v1 off", "name slot x in v1", YELLOW, "off"),
        ("Plain Database.xlsx", "grouping run is READ", "till last dash → SKU", GREEN, "match"),
        ("Packs Database.xlsx", "grouping run is READ", "whole SKU → Channel Child SKU", GREEN, "match"),
    ]
    for r, (col, do, used, bg, v1) in enumerate(rows, start=5):
        put(ws, r, 1, col, bold=True)
        put(ws, r, 2, do, bg=bg, align=C)
        put(ws, r, 3, used)
        put(ws, r, 4, v1, bg=bg, bold=True, align=C)
        ws.row_dimensions[r].height = 22
    put(ws, 22, 1, "Step 3: Order Grouping Sorter. SKU keys: CL after 1st dash | Plain till last dash | Packs whole. Attrs: Packs→CL→Plain. Packs colour later.", bg=GREEN, fg=GREEN_F, align=L)
    ws.merge_cells("A22:D22")
    widths(ws, {"A": 24, "B": 32, "C": 40, "D": 16})


def sheet_design(wb: Workbook) -> None:
    ws = wb.create_sheet("Design")
    ws.sheet_view.showGridLines = False
    put(ws, 1, 1, "Design grouping — off in v1. Different list per scenario.", bg=NAVY, fg=WHITE, bold=True, size=16, align=L)
    ws.merge_cells("A1:E1")
    put(ws, 2, 1, "When you turn it on, process name slot = group-01, group-02…  Fill a scenario before a run.", bg=BLUE, align=L)
    ws.merge_cells("A2:E2")
    for i, h in enumerate(["Scenario", "On (0/1)", "Group", "Logo / Design IDs", "Notes"]):
        put(ws, 4, 1 + i, h, bg=NAVY, fg=WHITE, bold=True, align=C)
    put(ws, 5, 1, "default (now)")
    put(ws, 5, 2, "0", bg=YELLOW, align=C)
    put(ws, 5, 3, "x", align=C)
    put(ws, 5, 4, "—", align=C)
    put(ws, 5, 5, "v1")
    put(ws, 6, 1, "CEO example")
    put(ws, 6, 2, "1", align=C)
    put(ws, 6, 3, "group-01", align=C)
    put(ws, 6, 4, "123LG, 245LG")
    put(ws, 6, 5, "sample only")
    for r in range(7, 16):
        for c in range(1, 6):
            put(ws, r, c, "")
    widths(ws, {"A": 20, "B": 12, "C": 14, "D": 36, "E": 22})


def main() -> None:
    wb = Workbook()
    sheet_board(wb)
    sheet_catalog(wb)
    sheet_design(wb)
    wb.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
