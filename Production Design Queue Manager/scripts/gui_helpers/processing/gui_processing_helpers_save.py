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
    import queue_app
    app_dir = os.path.dirname(os.path.abspath(queue_app.__file__))
    return os.path.join(app_dir, "Output", datetime.now().strftime("%Y-%m-%d"))


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


def create_rar_and_copy(gui, saved_file_paths: List[str], source_path: Optional[str], output_folder: str, dtf_queues_folder: Optional[str]) -> str:
    if not dtf_queues_folder:
        return ""
    try:
        from gui_helpers.common.gui_progress import update_progress
        from src.io.rar_utils import create_rar_from_pngs, generate_rar_name, copy_rar_to_dtf_queues
        update_progress(gui, 90, "Creating RAR archive...")
        rar_name = generate_rar_name([(fp, source_path) for fp in saved_file_paths], is_folder_processing=False)
        rar_path = os.path.join(output_folder, rar_name)
        success, result = create_rar_from_pngs(saved_file_paths, rar_path)
        if success:
            update_progress(gui, 95, "Copying RAR to DTF Queues folder...")
            copy_success, copy_result = copy_rar_to_dtf_queues(result, dtf_queues_folder)
            if copy_success:
                return f"\n\nRAR created and copied to DTF Queues folder:\n{os.path.basename(result)}"
            return f"\n\nRAR created but copy failed:\n{copy_result}"
        return f"\n\nRAR creation failed:\n{result}"
    except Exception as e:
        return f"\n\nRAR creation error: {str(e)}"
