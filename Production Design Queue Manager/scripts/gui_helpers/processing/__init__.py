"""GUI processing orchestration (arranging designs, folder processing)."""

from types import SimpleNamespace

from . import gui_processing_folder, gui_processing_coordination
from gui_helpers.reference import gui_size_reference

from .gui_processing_ui_single import process_single_file
from .gui_processing_ui_personalised import process_personalised_file
from .gui_processing_ui_missing_logo import process_missing_logo_file
from .gui_processing_core_single import process_single_file_for_folder
from .gui_processing_core_personalised import process_personalised_file_for_folder
from .gui_processing_core_missing_logo import process_missing_logo_file_for_folder
from .gui_processing_coordination import (
    arrange_designs,
    arrange_personalised_designs,
    arrange_missing_logo_designs,
)
from .gui_processing_folder import process_folder_personalised, process_folder

# Keep module-like exports expected by queue_app without wrapper files.
gui_processing_ui = SimpleNamespace(
    process_single_file=process_single_file,
    process_personalised_file=process_personalised_file,
    process_missing_logo_file=process_missing_logo_file,
)
gui_processing_core = SimpleNamespace(
    process_single_file_for_folder=process_single_file_for_folder,
    process_personalised_file_for_folder=process_personalised_file_for_folder,
    process_missing_logo_file_for_folder=process_missing_logo_file_for_folder,
)

__all__ = [
    "gui_processing_ui",
    "gui_processing_core",
    "gui_processing_folder",
    "gui_processing_coordination",
    "gui_size_reference",
    "arrange_designs",
    "arrange_personalised_designs",
    "arrange_missing_logo_designs",
    "process_folder_personalised",
    "process_folder",
]

