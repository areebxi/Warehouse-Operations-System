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

class DesignArrangerGUIMixin2:
    def select_single_designs_folder(self):
        """Select single design folder for personalised processing"""
        gui_file_selection.select_single_designs_folder(self)

    def select_double_designs_folder(self):
        """Select double design folder for personalised processing"""
        gui_file_selection.select_double_designs_folder(self)

    def select_dtf_queues_folder(self):
        """Select DTF Queues folder for RAR upload"""
        gui_file_selection.select_dtf_queues_folder(self)

    def remove_dtf_queues_folder(self):
        """Remove/clear DTF Queues folder directory"""
        gui_file_selection.remove_dtf_queues_folder(self)

    def update_canvas_size(self):
        """Update canvas dimensions"""
        gui_canvas_settings.update_canvas_size(self)

    def update_dpi(self):
        """Update DPI and recalculate mm to pixel conversion"""
        gui_canvas_settings.update_dpi(self)

    def extract_size_code(self, sku):
        """Extract size code from SKU by searching for size codes from the reference file"""
        return gui_size_reference.extract_size_code(self, sku)

    def sku_missing_cl_print_size(self, sku):
        """True when Item SKU has no print size in the CL database."""
        return gui_size_reference.sku_missing_cl_print_size(self, sku)

    def get_merged_text_from_reference(self, size_code):
        """Get Merged column text from Size Reference file (column I)"""
        return gui_size_reference.get_merged_text_from_reference(self, size_code)

    def save_missing_size_reference_rows(self, df, missing_row_indices, source_file_path=None):
        """Save rows with missing size references to a new DTF Des file"""
        return gui_size_reference.save_missing_size_reference_rows_func(self, df, missing_row_indices, source_file_path)

    def find_design_file(self, sku):
        """Find design file for given SKU"""
        return gui_utilities.find_design_file_wrapper(self, sku)

    def find_design_file_vba_logic(self, order_number, duplicate_index=0, folder_type=None, exclude_path=None):
        """Find design file following VBA logic: Single first, then Double"""
        return gui_utilities.find_design_file_vba_logic_wrapper(self, order_number, duplicate_index, folder_type, exclude_path)

    def update_progress(self, value, text=""):
        """Update progress bar and label"""
        update_progress_func(self, value, text)

    def reset_progress(self):
        """Reset progress bar"""
        reset_progress_func(self)

    def process_single_file(self, df, column, file_path=None, show_progress=True):
        """Process a single DTF Des file"""
        return gui_processing_ui.process_single_file(self, df, column, file_path, show_progress)

    def process_personalised_file(self, df, order_column, sku_column, file_path=None, show_progress=True):
        """Process a single file following VBA logic: Single first (with variations), then Double (EITHER/OR)"""
        return gui_processing_ui.process_personalised_file(self, df, order_column, sku_column, file_path, show_progress)

    def draw_preview(self):
        """Draw preview of arranged designs on canvas - shows all batches horizontally if multiple exist"""
        gui_preview.draw_preview(self)

    def on_mousewheel(self, event):
        """Scroll the preview canvas"""
        return gui_preview.on_mousewheel(self, event)

    def on_canvas_resize(self, event=None):
        """Debounced redraw when preview canvas is resized"""
        gui_preview.on_canvas_resize(self, event)

    def save_canvas_image(self):
        """Save the arranged canvas as an image file"""
        return gui_save.save_canvas_image(self)

    def save_folder_files_separately(self):
        """Save each file from folder processing separately with its own filename"""
        return gui_save.save_folder_files_separately(self)

    def clear_preview(self):
        """Clear preview canvas"""
        return gui_preview.clear_preview(self)

    def create_and_save_canvas(self, arranged_designs, save_path, batch_num=None, total_batches=None, source_file_path=None):
        """Create and save canvas image with arranged designs"""
        return gui_save.create_and_save_canvas(self, arranged_designs, save_path, batch_num, total_batches, source_file_path)

