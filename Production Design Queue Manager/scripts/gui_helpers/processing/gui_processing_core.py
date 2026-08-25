"""Compatibility module for split core processing flows."""

from .gui_processing_core_single import process_single_file_for_folder
from .gui_processing_core_personalised import process_personalised_file_for_folder
from .gui_processing_core_missing_logo import process_missing_logo_file_for_folder

__all__ = [
    "process_single_file_for_folder",
    "process_personalised_file_for_folder",
    "process_missing_logo_file_for_folder",
]
