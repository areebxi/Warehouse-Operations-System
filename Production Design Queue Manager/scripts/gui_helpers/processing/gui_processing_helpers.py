"""Compatibility re-export module for split processing helpers."""

from .gui_processing_helpers_messages import (
    create_design_log_entry,
    format_missing_items_list,
    handle_missing_designs_error,
    handle_missing_designs_warning,
    handle_missing_sizes_warning,
    is_plainlg_sku,
    is_customise_yes,
    track_missing_size_reference,
    track_missing_size_reference_multi,
)
from .gui_processing_helpers_arrangement import finalize_arrangement
from .gui_processing_helpers_folder import (
    auto_detect_order_column,
    auto_detect_sku_column,
    auto_detect_customise_column,
    build_processing_summary_message,
    find_dtf_des_files,
    load_dataframe_from_file,
    process_file_in_folder_missing_logo,
    process_file_in_folder_personalised,
    process_file_in_folder_standard,
)
from .gui_processing_helpers_folder_finalize import finalize_folder_processing

__all__ = [
    "create_design_log_entry",
    "format_missing_items_list",
    "handle_missing_designs_error",
    "handle_missing_designs_warning",
    "handle_missing_sizes_warning",
    "is_plainlg_sku",
    "is_customise_yes",
    "track_missing_size_reference",
    "track_missing_size_reference_multi",
    "finalize_arrangement",
    "auto_detect_order_column",
    "auto_detect_sku_column",
    "auto_detect_customise_column",
    "build_processing_summary_message",
    "find_dtf_des_files",
    "load_dataframe_from_file",
    "process_file_in_folder_missing_logo",
    "process_file_in_folder_personalised",
    "process_file_in_folder_standard",
    "finalize_folder_processing",
]
