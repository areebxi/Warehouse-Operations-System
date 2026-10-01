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
from queue_app_impl_mixin1 import DesignArrangerGUIMixin1
from queue_app_impl_mixin2 import DesignArrangerGUIMixin2

class DesignArrangerGUI(DesignArrangerGUIMixin1, DesignArrangerGUIMixin2):
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
        self.root.title("Production Design Queue Manager")
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
        self.input_file_path = None
        self.designs_folder = None
        self.single_designs_folder = None  # Single designs folder for personalised
        self.double_designs_folder = None  # Double designs folder for personalised
        self.dtf_queues_folder = None  # DTF Queues folder for RAR upload
        self.cl_csv_path = str(wh.cl_csv_path())
        self.config_workbook_path = str(wh.queue_config_workbook_path())
        self.size_reference_df = None  # archive sheet not used for live sizing
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
        self.input_folder_path = None  # legacy; unused (multi-file list replaces folder)
        self.input_file_paths = []  # selected DTF Des paths (Packing-style multi-select)
        self.folder_file_batches = {}  # Store batches for each file when processing: {file_path: [batches]}
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

        saved = self.saved_settings
        self.cl_csv_var = StringVar(
            value=(saved.get("cl_csv_path") or str(wh.cl_csv_path()))
        )
        self.config_workbook_var = StringVar(
            value=(saved.get("config_workbook_path") or str(wh.queue_config_workbook_path()))
        )
        
        # Auto-load Color Bar from app directory
        self.color_bar_image, self.color_bar_path = load_color_bar_from_app_dir()
        
        self._reload_data_sources()
        
        # Create UI
        self.create_ui()


        
        
    
    

    
    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
