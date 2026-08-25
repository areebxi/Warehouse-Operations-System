import os
import sys
import tkinter as tk
from PIL import Image

# Runtime packages are stored under scripts/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RUNTIME_MODULES_DIR = os.path.join(PROJECT_ROOT, "scripts")
if RUNTIME_MODULES_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_MODULES_DIR)

# Increase PIL image size limit to handle large canvases
Image.MAX_IMAGE_PIXELS = None  # Remove limit (or set to a very large number)

# Import new modules
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
    load_configuration_workbook,
)
from src.core import pack_designs, DEFAULT_DESIGN_PADDING

# Import GUI helper modules (consolidated)
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

# DTF Des File Format:
# DTF Des is an Excel Worksheet (.xlsx, .xls, or .csv) used to generate PNG files.
# It contains the following columns:
# - Order - Number
# - Item - Qty
# - Item - SKU
# - Item - Name
# - Ship To - Name
# - Notes - From Buyer
# - Ship To - Postal Code
# - Source
# - Process Num
# - Genre
# - Order Type
# - Orders Type Abbrevation
# - Condition

# Note: All module-level utility functions (save_error_to_file, setup_error_logging, etc.)
# have been moved to their respective modules (logging_utils, file_handlers, etc.)
# and are imported at the top of this file.

class DesignArrangerGUI:
    def __init__(self, root, settings_manager: Optional[SettingsManager] = None):
        """Initialize Queue App GUI.
        
        Args:
            root: Tkinter root window
            settings_manager: Optional SettingsManager instance. If None, creates one using DI.
                This allows dependency injection for testing and flexibility.
        """
        # Setup error logging first (each error/warning saved to separate file)
        setup_error_logging()
        
        self.root = root
        self.root.title("Queue App")
        # Ensure visible when launched via pythonw/start (can open iconified)
        self.root.deiconify()
        self.root.lift()
        # Open in maximized/fullscreen mode
        try:
            # Windows: use 'zoomed' state to maximize
            self.root.state('zoomed')
        except Exception:
            # Linux/Other: try to set fullscreen or maximize
            try:
                self.root.attributes('-zoomed', True)
            except Exception:
                # Fallback: get screen size and set geometry
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.minsize(1000, 600)  # Minimum window size for responsive design
        # Re-assert after idle in case the OS applied minimized after create
        self.root.after(0, self._ensure_window_visible)
        
        # Canvas dimensions in mm
        self.canvas_width_mm = 570
        self.canvas_height_mm = 3000
        self.dpi = 300  # DPI for printing (300 DPI is standard for high quality printing)
        self.mm_to_pixel = self.dpi / 25.4  # Convert mm to pixels
        
        # Data storage
        self.df = None
        self.designs_folder = None
        self.single_designs_folder = None  # Single designs folder for personalised
        self.double_designs_folder = None  # Double designs folder for personalised
        self.dtf_queues_folder = None  # DTF Queues folder for RAR upload
        self.size_reference_df = None
        self.size_reference_path = None
        # SKU Contain -> (width_mm, height_mm) from Override Print Size sheet
        self.print_size_overrides = {}
        # Legacy alias: set of SKU Contain tokens (for older call sites)
        self.pocket_design_ids_set = set()
        self.color_bar_path = None  # Color Bar file path
        self.color_bar_image = None  # Color Bar image
        self.arranged_designs = []
        self.all_batches = []  # Store all batches when designs exceed canvas height
        self.design_padding = DEFAULT_DESIGN_PADDING  # Horizontal padding (left/right) in pixels
        self._preview_photos = []
        self._preview_photo_cache = {}
        self.input_folder_path = None  # For folder selection
        self.folder_file_batches = {}  # Store batches for each file when processing folder: {file_path: [batches]}
        self.progress_var = None  # Progress bar variable
        self.progress_bar = None  # Progress bar widget
        self.progress_label = None  # Progress label widget
        self.is_personalised = False  # Flag to track if current arrangement is personalised
        
        # Settings manager - use dependency injection if provided, otherwise create via DI container
        if settings_manager is None:
            self.settings_manager = create_settings_manager()
        else:
            self.settings_manager = settings_manager
        self.saved_settings = self.settings_manager.saved_settings
        
        # Auto-load Color Bar from app directory
        self.color_bar_image, self.color_bar_path = load_color_bar_from_app_dir()
        
        # Auto-load Size Reference + Override Print Size from Configuration Workbook (one open)
        (
            self.size_reference_df,
            self.size_reference_path,
            self.print_size_overrides,
        ) = load_configuration_workbook()
        self.pocket_design_ids_set = set(self.print_size_overrides.keys())
        
        # Create UI
        self.create_ui()

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
        """Select a DTF Des file (Excel Worksheet containing order information)"""
        gui_file_selection.select_input_file(self)
    
    def select_input_folder(self):
        """Select a folder containing DTF Des files"""
        gui_file_selection.select_input_folder(self)
    
    def select_size_reference_file(self):
        """Select Size Reference file"""
        gui_file_selection.select_size_reference_file(self)
    
    def select_designs_folder(self):
        """Select designs folder"""
        gui_file_selection.select_designs_folder(self)
    
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
    
    def get_size_from_reference(self, size_code):
        """Get size dimensions from Size Reference file
        Returns Critical Width (column J) and Critical Height (column K) for logo scaling"""
        return gui_size_reference.get_size_from_reference(self, size_code)
    
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
    
    def update_progress(self, value, text=""):
        """Update progress bar and label"""
        update_progress_func(self, value, text)
    
    def reset_progress(self):
        """Reset progress bar"""
        reset_progress_func(self)
    
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
    
    def process_single_file(self, df, column, file_path=None, show_progress=True):
        """Process a single DTF Des file"""
        return gui_processing_ui.process_single_file(self, df, column, file_path, show_progress)
    
    def process_personalised_file(self, df, order_column, sku_column, file_path=None, show_progress=True):
        """Process a single file following VBA logic: Single first (with variations), then Double (EITHER/OR)"""
        return gui_processing_ui.process_personalised_file(self, df, order_column, sku_column, file_path, show_progress)
    
    def pack_designs(self, designs):
        """Pack designs on canvas with left designs left-aligned and right designs right-aligned
        Returns a list of batches, where each batch is a list of arranged designs"""
        return pack_designs(designs, self.canvas_width_mm, self.canvas_height_mm, self.mm_to_pixel, self.design_padding)
    
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
    
    def create_and_save_canvas(self, arranged_designs, save_path, batch_num=None, total_batches=None, source_file_path=None):
        """Create and save canvas image with arranged designs"""
        return gui_save.create_and_save_canvas(self, arranged_designs, save_path, batch_num, total_batches, source_file_path)
    
def main():
    # Setup console logging FIRST - captures all CMD output to file
    from src.system import setup_console_logging, close_console_logging
    console_log_path = setup_console_logging()
    if console_log_path:
        print(f"Console logging active. All output will be saved to: {console_log_path}")

    # Configure run logger verbosity (default is detailed; can be changed later)
    # For now, keep detailed logging enabled so every internal step is visible.
    set_detailed_logging(True)
    run_logger = get_run_logger()
    run_logger.info("Queue App run started. console_log_path=%s", console_log_path)
    
    # Setup error logging before creating GUI
    setup_error_logging()
    
    try:
        root = tk.Tk()
        DesignArrangerGUI(root)
        root.mainloop()
    finally:
        # Close console log file when application exits
        run_logger.info("Queue App run ending. Shutting down and closing console log.")
        close_console_logging()


if __name__ == "__main__":
    main()
