"""
RAR archive utilities for creating and managing RAR archives.

This module is the organized implementation that lives under `src/io/`.
"""
import os
import re
import subprocess
import shutil
from typing import Optional, List, Tuple, Union
from .rar_utils_create import (
    detect_rar_tool,
    _build_rar_command,
    _verify_archive_created,
    create_rar_from_pngs,
)
def _extract_name_part_from_source(source_file_path: str) -> Optional[str]:
    """Extract name part before first '-' from a source file path."""
    file_name = os.path.splitext(os.path.basename(source_file_path))[0]
    file_name = re.sub(r"^DTF\s*Des-", "", file_name, flags=re.IGNORECASE).strip()

    if "-" in file_name:
        name_part = file_name.split("-")[0].strip()
    else:
        name_part = file_name.strip()

    return name_part if name_part else None
def _generate_folder_processing_name(saved_files_info: List[Union[Tuple[str, ...], str]]) -> Optional[str]:
    """Generate RAR name for folder processing."""
    name_parts: List[str] = []
    source_files_seen: set[str] = set()

    for info in saved_files_info:
        if isinstance(info, tuple):
            source_file_path = info[1] if len(info) > 1 else None
        else:
            source_file_path = None

        if source_file_path:
            name_part = _extract_name_part_from_source(source_file_path)
            if name_part and name_part not in source_files_seen:
                name_parts.append(name_part)
                source_files_seen.add(name_part)

    if not name_parts:
        return None

    if len(name_parts) > 3:
        return "-".join(name_parts[:3]) + f"-and-{len(name_parts) - 3}-more.rar"
    return "-".join(name_parts) + ".rar"
def _generate_single_file_name(saved_files_info: List[Union[Tuple[str, ...], str]]) -> str:
    """Generate RAR name for single file processing."""
    if not saved_files_info:
        return "output.rar"

    first_file = saved_files_info[0]
    if isinstance(first_file, tuple):
        file_path = first_file[0]
        source_file_path = first_file[1] if len(first_file) > 1 else None
    else:
        file_path = first_file
        source_file_path = None

    if source_file_path:
        file_name = os.path.splitext(os.path.basename(source_file_path))[0]
        file_name = re.sub(r"^DTF\s*Des-", "", file_name, flags=re.IGNORECASE).strip()
    else:
        file_name = os.path.basename(file_path)
        file_name = re.sub(r"_Part \d+", "", file_name)
        file_name = os.path.splitext(file_name)[0]

    return f"{file_name}.rar"
def generate_rar_name(
    saved_files_info: List[Union[Tuple[str, ...], str]],
    is_folder_processing: bool = False,
) -> str:
    """Generate a RAR filename based on the processed files."""
    if is_folder_processing and saved_files_info:
        rar_name = _generate_folder_processing_name(saved_files_info)
        if rar_name:
            return rar_name

    return _generate_single_file_name(saved_files_info)
