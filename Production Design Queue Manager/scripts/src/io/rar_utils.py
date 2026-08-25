"""
RAR archive utilities for creating and managing RAR archives.

This module is the organized implementation that lives under `src/io/`.
"""

import os
import re
import subprocess
import shutil
from typing import Optional, List, Tuple, Union


def detect_rar_tool() -> Optional[str]:
    """Detect available RAR tool (WinRAR or 7-Zip)."""
    winrar_paths = [
        r"C:\Program Files\WinRAR\Rar.exe",
        r"C:\Program Files (x86)\WinRAR\Rar.exe",
    ]
    sevenzip_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]

    # First, check for WinRAR in PATH
    try:
        subprocess.run(["rar"], capture_output=True, timeout=2)
        return "rar"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    for path in winrar_paths:
        if os.path.exists(path):
            return path

    # If WinRAR not found, check for 7-Zip in PATH
    try:
        subprocess.run(["7z"], capture_output=True, timeout=2)
        return "7z"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    for path in sevenzip_paths:
        if os.path.exists(path):
            return path

    return None


def _build_rar_command(
    rar_tool: str,
    rar_path: str,
    png_names: List[str],
) -> Tuple[List[str], str, str]:
    """Build command for WinRAR/7-Zip and return cwd + actual archive path."""
    png_dir = os.path.dirname(rar_path) if os.path.dirname(rar_path) else os.getcwd()

    rar_tool_lower = (rar_tool or "").lower()
    if rar_tool == "rar" or "rar.exe" in rar_tool_lower or "winrar" in rar_tool_lower:
        cmd = [rar_tool, "a", "-ep1", "-y", rar_path] + png_names
        return cmd, png_dir, rar_path

    if rar_tool == "7z" or "7z.exe" in rar_tool_lower:
        rar_path_7z = rar_path.replace(".rar", ".7z")
        cmd = [rar_tool, "a", "-y", rar_path_7z] + png_names
        return cmd, png_dir, rar_path_7z

    raise ValueError(f"Unknown RAR tool: {rar_tool}")


def _verify_archive_created(
    rar_tool: str,
    rar_path: str,
    subprocess_result: subprocess.CompletedProcess,
) -> Tuple[bool, str]:
    """Verify archive was created successfully."""
    if subprocess_result.returncode != 0:
        error_msg = subprocess_result.stderr if subprocess_result.stderr else subprocess_result.stdout
        return False, f"RAR creation failed: {error_msg}"

    # If 7z was used, check for .7z file when rar extension requested
    if ("7z" in rar_tool.lower()) and rar_path.endswith(".rar"):
        rar_path_7z = rar_path.replace(".rar", ".7z")
        if os.path.exists(rar_path_7z):
            return True, rar_path_7z

    if os.path.exists(rar_path):
        return True, rar_path

    return False, "RAR file was not created"


def create_rar_from_pngs(png_files: List[str], rar_path: str) -> Tuple[bool, str]:
    """Create a RAR/7z archive from PNG files."""
    if not png_files:
        return False, "No PNG files to archive"

    rar_tool = detect_rar_tool()
    if not rar_tool:
        return False, "No RAR tool found. Please install WinRAR or 7-Zip."

    try:
        png_dir = os.path.dirname(png_files[0])
        png_names = [os.path.basename(png) for png in png_files]

        cmd, cwd, actual_archive_path = _build_rar_command(
            rar_tool,
            os.path.join(png_dir, os.path.basename(rar_path)),
            png_names,
        )

        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        return _verify_archive_created(rar_tool, actual_archive_path, result)
    except ValueError as e:
        return False, str(e)
    except subprocess.TimeoutExpired:
        return False, "RAR creation timed out"
    except Exception as e:
        return False, f"Error creating RAR: {str(e)}"


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

