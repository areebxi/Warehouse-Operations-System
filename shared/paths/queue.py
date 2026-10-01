from __future__ import annotations

from pathlib import Path

from shared.paths.root import DB_SLUG_QUEUE, database_app_dir, warehouse_root_from

def queue_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Production Design Queue Manager"


def queue_database_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_QUEUE, from_path)


def queue_data_dir(from_path: object | None = None) -> Path:
    """Alias for queue_database_dir (workbook lives here)."""
    return queue_database_dir(from_path)


def queue_config_workbook_path(from_path: object | None = None) -> Path:
    return queue_database_dir(from_path) / "Configuration Workbook.xlsx"


def queue_runtime_dir(from_path: object | None = None) -> Path:
    return queue_app_dir(from_path)


def queue_input_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Input"


def queue_output_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Output"


def queue_logs_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Logs"


def queue_missing_size_dir(from_path: object | None = None) -> Path:
    return queue_runtime_dir(from_path) / "Missing Size Reference"


def queue_config_dir(from_path: object | None = None) -> Path:
    return queue_app_dir(from_path) / "config"


def queue_settings_path(from_path: object | None = None) -> Path:
    return queue_config_dir(from_path) / "queue_app_settings.json"

__all__ = [
    "queue_app_dir",
    "queue_database_dir",
    "queue_data_dir",
    "queue_config_workbook_path",
    "queue_runtime_dir",
    "queue_input_dir",
    "queue_output_dir",
    "queue_logs_dir",
    "queue_missing_size_dir",
    "queue_config_dir",
    "queue_settings_path",
]
