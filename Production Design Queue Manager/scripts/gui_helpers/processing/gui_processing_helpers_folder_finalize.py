"""Folder processing finalization helper."""

from typing import List, Dict, Tuple, Union
from tkinter import messagebox
import pandas as pd
from .gui_processing_helpers_folder import build_processing_summary_message


def finalize_folder_processing(
    gui,
    all_combined_designs: List[Dict],
    all_missing_rows: List[Union[pd.DataFrame, Tuple[str, pd.DataFrame]]],
    success_count: int,
    failed_files: List[str],
) -> None:
    from gui_helpers.common.gui_progress import update_progress, reset_progress
    from gui_helpers.common import gui_theme
    if hasattr(gui, 'folder_file_batches') and gui.folder_file_batches:
        all_batches_combined = []
        for file_path, file_batches in gui.folder_file_batches.items():
            for batch in file_batches:
                all_batches_combined.append(list(batch))
        if all_batches_combined:
            gui.all_batches = all_batches_combined
            gui.arranged_designs = all_batches_combined[0] if all_batches_combined else []
        else:
            gui.all_batches = []
            gui.arranged_designs = []
        gui.draw_preview()
        total_designs = sum(len(batch) for batches in gui.folder_file_batches.values() for batch in batches)
        if len(gui.all_batches) > 1:
            gui.stats_label.config(
                text=f"{total_designs} designs from {success_count} file(s) in {len(gui.all_batches)} batches",
                foreground=gui_theme.FG,
            )
        else:
            gui.stats_label.config(
                text=f"{total_designs} designs from {success_count} file(s)",
                foreground=gui_theme.FG,
            )
    else:
        from src.core.canvas_arranger import pack_designs
        if all_combined_designs:
            update_progress(gui, 100, "Arranging all designs for preview...")
            batches = pack_designs(all_combined_designs, gui.canvas_width_mm, gui.canvas_height_mm, gui.mm_to_pixel, gui.design_padding)
            gui.all_batches = [list(batch) for batch in batches] if batches else []
            gui.arranged_designs = batches[0] if batches and len(batches) > 0 else []
            gui.draw_preview()
    if all_missing_rows:
        try:
            saved_files = []
            total_missing_rows = 0
            for entry in all_missing_rows:
                if isinstance(entry, tuple):
                    source_file_path, missing_df = entry
                else:
                    source_file_path, missing_df = None, entry
                total_missing_rows += len(missing_df)
                saved_file = gui.save_missing_size_reference_rows(
                    missing_df,
                    list(range(len(missing_df))),
                    source_file_path,
                )
                if saved_file:
                    saved_files.append(saved_file)
            if saved_files:
                files_list = "\n".join(saved_files[:10])
                if len(saved_files) > 10:
                    files_list += f"\n... and {len(saved_files) - 10} more"
                messagebox.showinfo(
                    "Missing Size References",
                    f"Found {total_missing_rows} rows with missing size references "
                    f"across {len(saved_files)} file(s).\n\nThese rows have been saved to:\n{files_list}",
                )
        except Exception as e:
            print(f"Error saving combined missing rows: {e}")
    total_designs = sum(len(batch) for batches in gui.folder_file_batches.values() for batch in batches) if hasattr(gui, 'folder_file_batches') and gui.folder_file_batches else (len(all_combined_designs) if all_combined_designs else 0)
    batches_count = len(gui.all_batches) if hasattr(gui, 'all_batches') and gui.all_batches else 0
    message = build_processing_summary_message(success_count, total_designs, batches_count, failed_files)
    messagebox.showinfo("Processing Complete", message)
    reset_progress(gui)
