from __future__ import annotations
import os
import re
import subprocess
import shutil
from typing import Optional, List, Tuple, Union

def copy_rar_to_dtf_queues(rar_path: str, dtf_queues_folder: Optional[str]) -> Tuple[bool, str]:
    """Copy a .rar/.7z to the configured DTF Queues folder."""
    if not dtf_queues_folder:
        return False, "DTF Queues folder not configured"

    if not os.path.exists(dtf_queues_folder):
        return False, f"DTF Queues folder does not exist: {dtf_queues_folder}"

    if not os.path.exists(rar_path):
        return False, f"RAR file does not exist: {rar_path}"

    try:
        rar_filename = os.path.basename(rar_path)
        dest_path = os.path.join(dtf_queues_folder, rar_filename)
        shutil.copy2(rar_path, dest_path)
        return True, dest_path
    except Exception as e:
        return False, f"Error copying RAR file: {str(e)}"
