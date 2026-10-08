"""ShipStationGUI class shell — methods live in run_script_gui_* helpers."""

from __future__ import annotations

import app_paths  # noqa: F401 — configures import paths before other local imports

import tkinter as tk
from tkinter import messagebox

from run_script_gui_db_ui import ShipStationGuiDbUiMixin
from run_script_gui_export import ShipStationGuiExportMixin
from run_script_gui_pdf import ShipStationGuiPdfMixin
from run_script_gui_run import ShipStationGuiRunMixin
from run_script_gui_settings import (
    effective_cl_csv_path,
    effective_packs_database_path,
    effective_plain_database_path,
    load_gui_settings,
    load_tag_mapping,
)
from run_script_gui_ui import ShipStationGuiUiMixin


class ShipStationGUI(
    ShipStationGuiExportMixin,
    ShipStationGuiRunMixin,
    ShipStationGuiPdfMixin,
    ShipStationGuiDbUiMixin,
    ShipStationGuiUiMixin,
):
    def __init__(self, root):
        self.root = root
        self.root.title("Purchase Order Generator")
        self.root.geometry("900x720")
        self.root.resizable(True, True)

        self.tag_name_var = tk.StringVar()
        self.pdf_copy_folder_var = tk.StringVar()
        self.cl_csv_var = tk.StringVar()
        self.plain_db_var = tk.StringVar()
        self.packs_db_var = tk.StringVar()
        self.selected_tag_id = None
        self.selected_tag_name = None
        self.is_running = False
        self.gui_settings = load_gui_settings()
        remembered = str(self.gui_settings.get("pdf_copy_folder") or "").strip()
        if remembered:
            self.pdf_copy_folder_var.set(remembered)
        self.cl_csv_var.set(str(effective_cl_csv_path(self.gui_settings)))
        self.plain_db_var.set(str(effective_plain_database_path(self.gui_settings)))
        self.packs_db_var.set(str(effective_packs_database_path(self.gui_settings)))

        self.tag_mapping = load_tag_mapping()
        if not self.tag_mapping:
            messagebox.showerror(
                "Error", "ShipStation Tags.xlsx file not found or could not be loaded!"
            )

        self.setup_ui()
