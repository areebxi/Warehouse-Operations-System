"""
Settings management for Queue App application.

This module provides the SettingsManager class for handling application settings
persistence. Settings are stored in a JSON file and can be loaded and saved
between application sessions.

Settings include:
    - input_file: Path to input file (for single file processing)
    - input_folder_path: Path to input folder (for folder processing)
    - size_reference_file: Path to size reference Excel file
    - designs_folder: Path to designs folder (for standard processing)
    - single_designs_folder: Path to single designs folder (for personalised mode)
    - double_designs_folder: Path to double designs folder (for personalised mode)
    - dtf_queues_folder: Path to DTF queues folder (for RAR export)
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from src.system.interfaces import ISettingsManager
def _get_project_root() -> str:
    """Resolve Queue app root from scripts/src/system module path."""
    return str(Path(__file__).resolve().parents[3])
def _warehouse_settings_path() -> Path:
    import sys

    app_root = Path(_get_project_root())
    warehouse = app_root.parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    return wh.queue_settings_path()
