"""Queue GUI action mixin — arrange / process / preview / save."""

from __future__ import annotations

from src.system.logging.run_logger import log_run_event
from src.core import pack_designs
from gui_helpers.ui import gui_canvas_settings
from gui_helpers.processing import gui_size_reference
from gui_helpers.preview import gui_preview
from gui_helpers.common import (
    gui_save,
    gui_utilities,
    update_progress as update_progress_func,
    reset_progress as reset_progress_func,
)


class DesignArrangerGUIActions:
    """Arrange / process / preview / save delegates."""

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

    def get_size_from_reference(self, size_code):
        """Get size dimensions from Size Reference file
        Returns Critical Width (column J) and Critical Height (column K) for logo scaling"""
        return gui_size_reference.get_size_from_reference(self, size_code)

    def get_merged_text_from_reference(self, size_code):
        """Get Merged column text from Size Reference file (column I)"""
        return gui_size_reference.get_merged_text_from_reference(self, size_code)

    def save_missing_size_reference_rows(self, df, missing_row_indices, source_file_path=None):
        """Save rows with missing size references to a new DTF Des file"""
        return gui_size_reference.save_missing_size_reference_rows_func(
            self, df, missing_row_indices, source_file_path
        )

    def find_design_file(self, sku):
        """Find design file for given SKU"""
        return gui_utilities.find_design_file_wrapper(self, sku)

    def find_design_file_vba_logic(
        self, order_number, duplicate_index=0, folder_type=None, exclude_path=None
    ):
        """Find design file following VBA logic: Single first, then Double"""
        return gui_utilities.find_design_file_vba_logic_wrapper(
            self, order_number, duplicate_index, folder_type, exclude_path
        )

    def arrange_missing_logo_designs(self):
        """Run: arrange selected DTF Des files (Customise column chooses folders)."""
        log_run_event("mode_selected", mode="run")
        from gui_helpers.processing import arrange_missing_logo_designs

        arrange_missing_logo_designs(self)

    def update_progress(self, value, text=""):
        """Update progress bar and label"""
        update_progress_func(self, value, text)

    def reset_progress(self):
        """Reset progress bar"""
        reset_progress_func(self)

    def pack_designs(self, designs):
        """Pack designs on canvas with left designs left-aligned and right designs right-aligned
        Returns a list of batches, where each batch is a list of arranged designs"""
        return pack_designs(
            designs,
            self.canvas_width_mm,
            self.canvas_height_mm,
            self.mm_to_pixel,
            self.design_padding,
        )

    def draw_preview(self):
        """Draw preview of arranged designs on canvas - shows all batches horizontally if multiple exist"""
        gui_preview.draw_preview(self)

    def on_mousewheel(self, event):
        """Scroll the preview canvas"""
        return gui_preview.on_mousewheel(self, event)

    def on_canvas_resize(self, event=None):
        """Debounced redraw when preview canvas is resized"""
        gui_preview.on_canvas_resize(self, event)

    def save_canvas_for_file(self, batches, file_path):
        """Save canvas for a specific file (used in folder processing)
        batches: list of batches, each batch is a list of arranged designs"""
        return gui_save.save_canvas_for_file(self, batches, file_path)

    def save_canvas_image(self):
        """Save the arranged canvas as an image file"""
        return gui_save.save_canvas_image(self)

    def save_folder_files_separately(self):
        """Save each file from folder processing separately with its own filename"""
        return gui_save.save_folder_files_separately(self)

    def clear_preview(self):
        """Clear preview canvas"""
        return gui_preview.clear_preview(self)

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

    def create_and_save_canvas(
        self,
        arranged_designs,
        save_path,
        batch_num=None,
        total_batches=None,
        source_file_path=None,
    ):
        """Create and save canvas image with arranged designs"""
        return gui_save.create_and_save_canvas(
            self,
            arranged_designs,
            save_path,
            batch_num,
            total_batches,
            source_file_path,
        )
