from __future__ import annotations
import os
from tkinter import messagebox
from .gui_processing_core_single import (
    process_single_file_for_folder,
)
from .gui_processing_core_personalised import (
    process_personalised_file_for_folder,
)
from .gui_processing_core_missing_logo import (
    process_missing_logo_file_for_folder,
)
from gui_helpers.common.gui_progress import update_progress
from .gui_processing_helpers_folder import (
    get_selected_input_files,
    load_dataframe_from_file,
    process_file_in_folder_standard,
    process_file_in_folder_personalised,
    process_file_in_folder_missing_logo,
)
from .gui_processing_helpers_folder_finalize import (
    finalize_folder_processing,
)

def process_folder(gui):
    """Process all selected DTF Des files (multi-file / batch).

    DTF Des files are Excel Worksheets (.xlsx, .xls, or .csv) containing order information
    with columns: Order - Number, Item - Qty, Item - SKU, Item - Name, Ship To - Name,
    Notes - From Buyer, Ship To - Postal Code, Source, Process Num, Genre, Order Type,
    Orders Type Abbrevation, Condition
    """
    excel_files = get_selected_input_files(gui)
    if not excel_files:
        messagebox.showwarning("Warning", "Please select DTF Des file(s) first!")
        return

    if not gui.designs_folder:
        messagebox.showwarning("Warning", "Please select a designs folder first!")
        return

    gui.folder_file_batches = {}

    # Process each file and collect all designs for combined preview
    success_count = 0
    failed_files = []
    total_files = len(excel_files)
    all_combined_designs = []  # Collect all designs from all files for preview
    all_missing_rows = []  # Collect all missing rows from all files

    update_progress(gui, 0, f"Processing 0/{total_files} files...")

    for idx, file_path in enumerate(excel_files):
        progress = (idx / total_files) * 100
        update_progress(gui, progress, f"Processing {idx+1}/{total_files}: {os.path.basename(file_path)}")

        # Load file
        df = load_dataframe_from_file(file_path)

        # Process this file
        file_designs, file_batches, missing_row_indices, error_msg = process_file_in_folder_standard(
            gui, file_path, df, process_single_file_for_folder
        )

        if error_msg:
            failed_files.append(error_msg)
            continue

        # Collect missing rows from this file
        if missing_row_indices:
            missing_rows = df.iloc[missing_row_indices].copy()
            all_missing_rows.append((file_path, missing_rows))

        # Store batches for this file (for separate saving later)
        if file_batches:
            gui.folder_file_batches[file_path] = file_batches

        # Collect designs from this file for combined preview
        if file_designs:
            all_combined_designs.extend(file_designs)

        success_count += 1

    update_progress(gui, 100, f"Completed: {success_count}/{total_files} files processed")

    # Finalize processing: arrange designs, update UI, save missing rows, show summary
    finalize_folder_processing(gui, all_combined_designs, all_missing_rows, success_count, failed_files)
