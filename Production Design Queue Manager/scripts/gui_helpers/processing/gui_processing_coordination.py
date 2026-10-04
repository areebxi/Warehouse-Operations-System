"""GUI Run coordination — single entry for selected DTF Des file(s)."""

from tkinter import messagebox

from gui_helpers.common.gui_demo_mode import (
    has_missing_logo_folders,
    queue_demo_lookup,
)
from .gui_processing_folder import process_folder_missing_logo
from .gui_processing_helpers_folder import get_selected_input_files


def arrange_missing_logo_designs(gui):
    """Run: Arrange selected files using Customise-column folder routing."""
    if not get_selected_input_files(gui):
        messagebox.showwarning("Warning", "Please select DTF Des file(s) first!")
        return
    if not has_missing_logo_folders(gui):
        messagebox.showwarning(
            "Warning",
            "Please select design folders first "
            "(Normal and/or Customise Single/Double — Run uses Customise column to choose).",
        )
        return
    with queue_demo_lookup(gui):
        process_folder_missing_logo(gui)
