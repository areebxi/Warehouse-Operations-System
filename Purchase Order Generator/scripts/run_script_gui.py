"""
GUI for the updated run_script.py flow (Awaiting Dispatch + Specific Tag)
Reuses helpers from run_script.py and matches pack/process-no logic and outputs.
"""

import app_paths  # noqa: F401 — configures import paths before other local imports

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import sys
import csv
import json
import shutil
from datetime import datetime
import openpyxl

from ftplib import FTP, error_perm, error_temp, error_reply  # noqa: F401 (for parity logging)

# Reuse original modules and helpers
from shipstation_orders import ShipStationAPI, ShipStationError
from app_paths import DATA_DIR, asset_path, data_path, shipstation_tags_path, tag_output_dir
from pdf_generator import generate_packing_slips_for_tag

GUI_SETTINGS_PATH = DATA_DIR / "gui_settings.json"

# Import helpers from run_script.py
from run_script import (
    get_process_no_for_tag,
    pdf_filename_for_tag,
    load_packs_database,
    load_pack_names,
    download_ftp_file,
    load_stock_levels,
    _stock_file_paths,
    load_custom_label_stock_map,
    validate_orders_stock,
    write_packing_list_csv,
    write_edi_orders_csv,
    write_stock_issues_csv,
    format_run_summary,
    rows_for_pdf_slips,
)
from run_script_gui_impl import ShipStationGUI


def load_gui_settings() -> dict:
    """Load remembered GUI settings (e.g. PDF copy folder)."""
    try:
        if GUI_SETTINGS_PATH.exists():
            with open(GUI_SETTINGS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"[WARNING] Could not load GUI settings: {e}")
    return {}


def save_gui_settings(settings: dict) -> None:
    """Persist GUI settings to data/gui_settings.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(GUI_SETTINGS_PATH, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
    except Exception as e:
        print(f"[WARNING] Could not save GUI settings: {e}")


def load_tag_mapping():
    """
    Load Tag Name → Tag ID from ShipStation Tags.xlsx.
    Column B: Tag Name, Column C: Tag ID
    """
    tag_mapping = {}
    try:
        xlsx_path = str(shipstation_tags_path())
        if not os.path.exists(xlsx_path):
            print(f"[WARNING] ShipStation Tags.xlsx not found at: {xlsx_path}")
            return tag_mapping

        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2):  # Skip header row
            tag_name_cell = row[1]  # Column B (0-based index 1)
            tag_id_cell = row[2]    # Column C (0-based index 2)
            
            tag_name = "" if tag_name_cell.value is None else str(tag_name_cell.value).strip()
            tag_id = "" if tag_id_cell.value is None else str(tag_id_cell.value).strip()
            
            if tag_name and tag_id:
                tag_mapping[tag_name] = tag_id
                
        return tag_mapping
    except Exception as e:
        print(f"[ERROR] Error loading tag mapping: {e}")
        return tag_mapping


def main():
    root = tk.Tk()
    ShipStationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


