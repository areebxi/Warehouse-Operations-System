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

class ShipStationGUIMixin3:
    def browse_pdf_copy_folder(self):
        """Let the user pick a folder; remember it for later runs."""
        initial = self.pdf_copy_folder_var.get().strip()
        if not initial or not os.path.isdir(initial):
            initial = None
        chosen = filedialog.askdirectory(
            title="Select PDF copy folder",
            initialdir=initial or None,
            mustexist=True,
        )
        if not chosen:
            return
        self.pdf_copy_folder_var.set(chosen)
        self.gui_settings["pdf_copy_folder"] = chosen
        save_gui_settings(self.gui_settings)
        self.log_message(f"[SETTINGS] PDF copy folder set to: {chosen}")

    def clear_pdf_copy_folder(self):
        """Clear the remembered PDF copy folder."""
        if not self.pdf_copy_folder_var.get().strip() and not self.gui_settings.get("pdf_copy_folder"):
            self.log_message("[SETTINGS] No PDF copy folder to remove.")
            return
        self.pdf_copy_folder_var.set("")
        self.gui_settings.pop("pdf_copy_folder", None)
        save_gui_settings(self.gui_settings)
        self.log_message("[SETTINGS] PDF copy folder removed.")

    def log_message(self, message: str):
        self.logs_text.insert(tk.END, f"{message}\n")
        self.logs_text.see(tk.END)
        self.root.update_idletasks()

