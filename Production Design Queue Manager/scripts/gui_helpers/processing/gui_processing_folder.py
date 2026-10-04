"""Multi-file folder processing for Queue Run (Customise-column routing)."""

import os
from tkinter import messagebox

from .gui_processing_core_missing_logo import process_missing_logo_file_for_folder
from gui_helpers.common.gui_progress import update_progress
from .gui_processing_helpers_folder import (
    get_selected_input_files,
    load_dataframe_from_file,
    process_file_in_folder_missing_logo,
)
from .gui_processing_helpers_folder_finalize import finalize_folder_processing


def process_folder_missing_logo(gui):
    """Process all selected DTF Des files using Run mode (Customise routing)."""
    excel_files = get_selected_input_files(gui)
    if not excel_files:
        messagebox.showwarning("Warning", "Please select DTF Des file(s) first!")
        return

    if not gui.single_designs_folder and not gui.double_designs_folder and not gui.designs_folder:
        messagebox.showwarning(
            "Warning",
            "Please select at least one folder (Single/Double Design Folder or Designs Folder)!",
        )
        return

    gui.folder_file_batches = {}

    success_count = 0
    failed_files = []
    total_files = len(excel_files)
    all_combined_designs = []
    all_missing_rows = []

    update_progress(gui, 0, f"Processing 0/{total_files} files...")

    for idx, file_path in enumerate(excel_files):
        progress = (idx / total_files) * 100
        update_progress(
            gui, progress, f"Processing {idx + 1}/{total_files}: {os.path.basename(file_path)}"
        )

        df = load_dataframe_from_file(file_path)
        file_designs, file_batches, missing_row_indices, error_msg = (
            process_file_in_folder_missing_logo(
                gui, file_path, df, process_missing_logo_file_for_folder
            )
        )

        if error_msg:
            failed_files.append(error_msg)
            continue

        if missing_row_indices:
            missing_rows = df.iloc[missing_row_indices].copy()
            all_missing_rows.append((file_path, missing_rows))

        if file_batches:
            gui.folder_file_batches[file_path] = file_batches

        if file_designs:
            all_combined_designs.extend(file_designs)

        success_count += 1

    update_progress(gui, 100, f"Completed: {success_count}/{total_files} files processed")
    finalize_folder_processing(
        gui, all_combined_designs, all_missing_rows, success_count, failed_files
    )
