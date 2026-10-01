from __future__ import annotations
import os
import sys
import tkinter as tk
from tkinter import StringVar
from PIL import Image
from shared import paths as wh  # noqa: E402
from src.system import (
    setup_error_logging,
    get_run_logger,
    set_detailed_logging,
    SettingsManager,
    create_settings_manager,
)
from src.system.logging.run_logger import log_run_event
from typing import Optional
from src.io import (
    load_color_bar_from_app_dir,
    load_queue_data_sources,
)
from src.core import pack_designs, DEFAULT_DESIGN_PADDING
from gui_helpers.ui import (
    gui_file_selection,
    gui_settings,
    gui_canvas_settings,
    create_ui as create_ui_func,
)
from gui_helpers.processing import (
    gui_processing_ui,
    gui_processing_core,
    gui_size_reference,
)
from gui_helpers.preview import gui_preview
from gui_helpers.common import (
    gui_save,
    gui_utilities,
    update_progress as update_progress_func,
    reset_progress as reset_progress_func,
)

class DesignArrangerGUIMixin1:
    def _ensure_window_visible(self):
        """Force the main window out of a minimized/iconified state after launch."""
        try:
            self.root.deiconify()
            self.root.state('zoomed')
            self.root.lift()
            self.root.focus_force()
        except Exception:
            try:
                self.root.deiconify()
                self.root.lift()
            except Exception:
                pass

    def process_folder(self):
        """Process all DTF Des files in selected folder

        DTF Des files are Excel Worksheets (.xlsx, .xls, or .csv) containing order information
        with columns: Order - Number, Item - Qty, Item - SKU, Item - Name, Ship To - Name,
        Notes - From Buyer, Ship To - Postal Code, Source, Process Num, Genre, Order Type,
        Orders Type Abbrevation, Condition
        """
        log_run_event("mode_selected", mode="folder_standard")
        from gui_helpers.processing import process_folder
        process_folder(self)

    def _reload_data_sources(self) -> None:
        """Reload CL print sizes + workbook pocket overrides from GUI paths."""
        self.cl_csv_path, self.print_size_overrides, self.config_workbook_path = (
            load_queue_data_sources(
                self.cl_csv_var.get(),
                self.config_workbook_var.get(),
            )
        )
        self.pocket_design_ids_set = set(self.print_size_overrides.keys())

    def arrange_designs(self):
        """Coordinate arranging designs (standard mode)"""
        log_run_event("mode_selected", mode="standard")
        from gui_helpers.processing import arrange_designs
        arrange_designs(self)

    def arrange_personalised_designs(self):
        """Coordinate arranging personalised designs"""
        log_run_event("mode_selected", mode="personalised")
        from gui_helpers.processing import arrange_personalised_designs
        arrange_personalised_designs(self)

    def arrange_missing_logo_designs(self):
        """Coordinate arranging designs with Missing Logo mode (personalized first, then all in one go)"""
        log_run_event("mode_selected", mode="missing_logo")
        from gui_helpers.processing import arrange_missing_logo_designs
        arrange_missing_logo_designs(self)

    def process_folder_personalised(self):
        """Process all DTF Des files in selected folder using personalised mode"""
        log_run_event("mode_selected", mode="folder_personalised")
        from gui_helpers.processing import process_folder_personalised
        process_folder_personalised(self)

    def process_single_file_for_folder(self, df, column, file_path):
        """Process a single DTF Des file for folder processing
        Returns: (designs_list, batches_list, missing_row_indices)
        """
        return gui_processing_core.process_single_file_for_folder(self, df, column, file_path)

    def process_personalised_file_for_folder(self, df, order_column, sku_column, file_path):
        """Process a single DTF Des file for folder processing in personalised mode
        Returns: (designs_list, batches_list, missing_row_indices)
        """
        return gui_processing_core.process_personalised_file_for_folder(self, df, order_column, sku_column, file_path)

    def get_size_from_reference(self, size_code):
        """Get size dimensions from Size Reference file
        Returns Critical Width (column J) and Critical Height (column K) for logo scaling"""
        return gui_size_reference.get_size_from_reference(self, size_code)

    def pack_designs(self, designs):
        """Pack designs on canvas with left designs left-aligned and right designs right-aligned
        Returns a list of batches, where each batch is a list of arranged designs"""
        return pack_designs(designs, self.canvas_width_mm, self.canvas_height_mm, self.mm_to_pixel, self.design_padding)

    def save_canvas_for_file(self, batches, file_path):
        """Save canvas for a specific file (used in folder processing)
        batches: list of batches, each batch is a list of arranged designs"""
        return gui_save.save_canvas_for_file(self, batches, file_path)

    def create_rar_from_pngs(self, png_files, rar_path):
        """Create RAR archive from PNG files"""
        from src.io import create_rar_from_pngs
        return create_rar_from_pngs(png_files, rar_path)

    def generate_rar_name(self, saved_files_info, is_folder_processing=False):
        """Generate RAR filename based on saved files"""
        from src.io import generate_rar_name
        return generate_rar_name(saved_files_info, is_folder_processing)

    def copy_rar_to_dtf_queues(self, rar_path, dtf_queues_folder):
        """Copy RAR file to DTF Queues folder"""
        from src.io import copy_rar_to_dtf_queues
        return copy_rar_to_dtf_queues(rar_path, dtf_queues_folder)

    def create_ui(self):
        """Create the main UI for the Queue App application"""
        create_ui_func(self)

    def save_settings(self):
        """Save current settings to file"""
        gui_settings.save_settings(self)

    def auto_load_settings(self):
        """Auto-load saved file and folder paths"""
        gui_settings.auto_load_settings(self)

    def select_input_file(self):
        """Compatibility alias — Add DTF Des file(s)."""
        gui_file_selection.add_input_files(self)

    def add_input_files(self):
        """Add one or more DTF Des files (multi-select)."""
        gui_file_selection.add_input_files(self)

    def remove_selected_input_files(self):
        """Remove highlighted input files from the list."""
        gui_file_selection.remove_selected_input_files(self)

    def remove_all_input_files(self):
        """Clear all selected input files."""
        gui_file_selection.remove_all_input_files(self)

    def select_size_reference_file(self):
        """Legacy alias — select Configuration Workbook."""
        self.select_config_workbook()

    def select_cl_csv(self):
        """Select Custom Label Database CSV for print sizes."""
        gui_file_selection.select_cl_csv(self)

    def select_config_workbook(self):
        """Select Configuration Workbook."""
        gui_file_selection.select_config_workbook(self)

    def select_designs_folder(self):
        """Select designs folder"""
        gui_file_selection.select_designs_folder(self)

