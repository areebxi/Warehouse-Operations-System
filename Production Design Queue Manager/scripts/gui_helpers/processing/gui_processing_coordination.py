"""
GUI processing coordination functions.

Moved into `gui_helpers/processing/` to keep the codebase organized.
"""

from tkinter import messagebox

from gui_helpers.common.gui_demo_mode import (
    has_missing_logo_folders,
    has_normal_folder,
    has_personalised_folders,
    queue_demo_lookup,
)
from .gui_processing_folder import (
    process_folder,
    process_folder_personalised,
    process_folder_missing_logo,
)
from .gui_processing_helpers_folder import get_selected_input_files


def _require_input_files(gui) -> bool:
    if get_selected_input_files(gui):
        return True
    messagebox.showwarning("Warning", "Please select DTF Des file(s) first!")
    return False


def arrange_designs(gui):
    """Coordinate arranging designs (standard mode)."""
    if not _require_input_files(gui):
        return
    if not has_normal_folder(gui):
        messagebox.showwarning("Warning", "Please select a designs folder first!")
        return
    with queue_demo_lookup(gui):
        process_folder(gui)


def arrange_personalised_designs(gui):
    """Coordinate arranging personalised designs."""
    if not _require_input_files(gui):
        return
    if not has_personalised_folders(gui):
        messagebox.showwarning("Warning", "Please select Single and Double Design folders first!")
        return
    with queue_demo_lookup(gui):
        process_folder_personalised(gui)


def arrange_missing_logo_designs(gui):
    """Coordinate arranging designs with Missing Logo / Run mode."""
    if not _require_input_files(gui):
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
