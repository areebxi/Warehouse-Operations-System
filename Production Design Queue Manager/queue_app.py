import os
import sys
import tkinter as tk
from tkinter import StringVar
from PIL import Image

# Runtime packages are stored under scripts/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RUNTIME_MODULES_DIR = os.path.join(PROJECT_ROOT, "scripts")
if RUNTIME_MODULES_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_MODULES_DIR)
WAREHOUSE_ROOT = os.path.dirname(PROJECT_ROOT)
if str(WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(WAREHOUSE_ROOT))

from shared import paths as wh  # noqa: E402

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
    load_queue_data_sources,
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
from queue_app_impl import DesignArrangerGUI

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
