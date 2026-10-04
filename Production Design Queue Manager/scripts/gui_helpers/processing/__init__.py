"""GUI processing orchestration (Run / arrange designs)."""

from types import SimpleNamespace

from . import gui_processing_folder, gui_processing_coordination
from gui_helpers.reference import gui_size_reference

from .gui_processing_core_missing_logo import process_missing_logo_file_for_folder
from .gui_processing_coordination import arrange_missing_logo_designs
from .gui_processing_folder import process_folder_missing_logo

gui_processing_core = SimpleNamespace(
    process_missing_logo_file_for_folder=process_missing_logo_file_for_folder,
)

__all__ = [
    "gui_processing_core",
    "gui_processing_folder",
    "gui_processing_coordination",
    "gui_size_reference",
    "arrange_missing_logo_designs",
    "process_folder_missing_logo",
]
