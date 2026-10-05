"""Save/output helpers for processing flows."""

import os
import re
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from tkinter import messagebox


def extract_input_file_name(gui) -> str:
    input_file_name = "output"
    if hasattr(gui, 'input_file_path') and gui.input_file_path:
        input_file_name = os.path.splitext(os.path.basename(gui.input_file_path))[0]
    return re.sub(r'^DTF\s*Des-', '', input_file_name, flags=re.IGNORECASE).strip()


def get_output_folder() -> str:
    import sys
    from pathlib import Path

    warehouse = Path(__file__).resolve().parents[3].parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    return str(wh.queue_output_dir() / datetime.now().strftime("%Y-%m-%d"))


def create_output_folder_safe(output_folder: str) -> bool:
    try:
        os.makedirs(output_folder, exist_ok=True)
        return True
    except Exception:
        return False


def generate_save_file_paths(batches: List[List[Dict]], input_file_name: str, output_folder: str) -> List[Tuple]:
    files_to_save = []
    for batch_num, batch in enumerate(batches, 1):
        if len(batches) > 1:
            file_path = os.path.join(output_folder, f"{input_file_name}_Part {batch_num}.png")
        else:
            file_path = os.path.join(output_folder, f"{input_file_name}.png")
        files_to_save.append((batch, file_path, batch_num, len(batches)))
    return files_to_save


def check_and_confirm_file_overwrite(files_to_save: List[Tuple]) -> bool:
    existing_files = [fp for _, fp, _, _ in files_to_save if os.path.exists(fp)]
    if existing_files:
        return messagebox.askyesno("File Exists", f"{len(existing_files)} file(s) already exist(s).\n\nDo you want to overwrite them?")
    return True


def copy_pngs_to_queues(
    gui,
    saved_file_paths: List[str],
    dtf_queues_folder: Optional[str],
) -> str:
    """Copy saved PNGs to DTF Queues folder when configured. Returns UI suffix text."""
    if not dtf_queues_folder:
        return ""
    try:
        from gui_helpers.common.gui_progress import update_progress
        from src.io.dtf_queues_copy import copy_pngs_to_dtf_queues

        update_progress(gui, 95, "Copying PNGs to DTF Queues folder...")
        success, result = copy_pngs_to_dtf_queues(saved_file_paths, dtf_queues_folder)
        if success:
            return f"\n\nPNGs copied to DTF Queues folder:\n{result}"
        return f"\n\nPNG copy to DTF Queues failed:\n{result}"
    except Exception as e:
        return f"\n\nPNG copy to DTF Queues error: {str(e)}"
