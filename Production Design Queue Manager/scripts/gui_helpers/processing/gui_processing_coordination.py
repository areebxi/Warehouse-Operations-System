"""
GUI processing coordination functions.

Moved into `gui_helpers/processing/` to keep the codebase organized.
"""

import pandas as pd
from tkinter import messagebox

from .gui_processing_ui import (
    process_single_file,
    process_personalised_file,
    process_missing_logo_file,
)
from .gui_processing_folder import (
    process_folder,
    process_folder_personalised,
    process_folder_missing_logo,
)
from .gui_processing_helpers import auto_detect_sku_column, auto_detect_order_column


def arrange_designs(gui):
    """Coordinate arranging designs (standard mode)."""
    # Check if folder is selected
    if gui.input_folder_path:
        process_folder(gui)
        return

    # Process single file
    if gui.df is None:
        messagebox.showwarning("Warning", "Please select an input file or folder first!")
        return

    if not gui.designs_folder:
        messagebox.showwarning("Warning", "Please select a designs folder first!")
        return

    # Auto-detect Item SKU column
    column = auto_detect_sku_column(gui.df)
    if not column:
        messagebox.showwarning("Warning", "No SKU column found! Please check your DTF Des file.")
        return

    # Process single file
    process_single_file(gui, gui.df, column, getattr(gui, "input_file_path", None))


def arrange_personalised_designs(gui):
    """Coordinate arranging personalised designs."""
    # Check if folder is selected
    if gui.input_folder_path:
        process_folder_personalised(gui)
        return

    # Check if input file is selected
    if gui.df is None:
        messagebox.showwarning("Warning", "Please select an input file or folder first!")
        return

    # Check if single and double folders are selected
    if not gui.single_designs_folder:
        messagebox.showwarning("Warning", "Please select a Single Design Folder first!")
        return

    if not gui.double_designs_folder:
        messagebox.showwarning("Warning", "Please select a Double Design Folder first!")
        return

    # Auto-detect Order Number column
    order_column = auto_detect_order_column(gui.df)
    if not order_column:
        messagebox.showwarning("Warning", "No Order Number column found! Please check your DTF Des file.")
        return

    # Auto-detect Item SKU column
    sku_column = auto_detect_sku_column(gui.df)
    if not sku_column:
        messagebox.showwarning("Warning", "No Item SKU column found! Please check your DTF Des file.")
        return

    # Process with Order Number (for design files) and Item SKU (for size)
    process_personalised_file(
        gui,
        gui.df,
        order_column,
        sku_column,
        getattr(gui, "input_file_path", None),
    )


def arrange_missing_logo_designs(gui):
    """Coordinate arranging designs with Missing Logo mode."""
    # Check if folder is selected
    if gui.input_folder_path:
        process_folder_missing_logo(gui)
        return

    # Check if input file is selected
    if gui.df is None:
        messagebox.showwarning("Warning", "Please select an input file or folder first!")
        return

    # Check if at least one folder is selected (personalized or all in one go)
    if not gui.single_designs_folder and not gui.double_designs_folder and not gui.designs_folder:
        messagebox.showwarning(
            "Warning",
            "Please select at least one folder (Single/Double Design Folder or Designs Folder)!",
        )
        return

    # Auto-detect Order Number column
    order_column = auto_detect_order_column(gui.df)
    if not order_column:
        messagebox.showwarning("Warning", "No Order Number column found! Please check your DTF Des file.")
        return

    # Auto-detect Item SKU column
    sku_column = auto_detect_sku_column(gui.df)
    if not sku_column:
        messagebox.showwarning("Warning", "No Item SKU column found! Please check your DTF Des file.")
        return

    # Process with Order Number (for design files) and Item SKU (for size)
    process_missing_logo_file(
        gui,
        gui.df,
        order_column,
        sku_column,
        getattr(gui, "input_file_path", None),
    )

