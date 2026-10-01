from __future__ import annotations
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
from shipstation_orders import ShipStationAPI, ShipStationError
from app_paths import DATA_DIR, asset_path, data_path, shipstation_tags_path, tag_output_dir
from pdf_generator import generate_packing_slips_for_tag
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
from run_script_gui_impl_mixin1 import ShipStationGUIMixin1
from run_script_gui_impl_mixin2 import ShipStationGUIMixin2
from run_script_gui_impl_mixin3 import ShipStationGUIMixin3

class ShipStationGUI(ShipStationGUIMixin1, ShipStationGUIMixin2, ShipStationGUIMixin3):
    def __init__(self, root):
        self.root = root
        self.root.title("Purchase Order Generator")
        self.root.geometry("800x640")
        self.root.resizable(True, True)

        self.tag_name_var = tk.StringVar()
        self.pdf_copy_folder_var = tk.StringVar()
        self.selected_tag_id = None
        self.selected_tag_name = None
        self.is_running = False
        self.gui_settings = load_gui_settings()
        remembered = str(self.gui_settings.get("pdf_copy_folder") or "").strip()
        if remembered:
            self.pdf_copy_folder_var.set(remembered)

        # Load tag mapping
        self.tag_mapping = load_tag_mapping()
        if not self.tag_mapping:
            messagebox.showerror("Error", "ShipStation Tags.xlsx file not found or could not be loaded!")

        self.setup_ui()


