"""Compatibility module for split UI processing flows."""

from .gui_processing_ui_single import process_single_file
from .gui_processing_ui_personalised import process_personalised_file
from .gui_processing_ui_missing_logo import process_missing_logo_file

__all__ = [
    "process_single_file",
    "process_personalised_file",
    "process_missing_logo_file",
]
