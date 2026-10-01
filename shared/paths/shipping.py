from __future__ import annotations

from pathlib import Path

from shared.paths.root import DB_SLUG_SHIPPING, database_app_dir, warehouse_root_from

def shipping_app_dir(from_path: object | None = None) -> Path:
    return warehouse_root_from(from_path) / "Shipping Label Generator"


def shipping_database_dir(from_path: object | None = None) -> Path:
    return database_app_dir(DB_SLUG_SHIPPING, from_path)


def shipping_runtime_dir(from_path: object | None = None) -> Path:
    return shipping_app_dir(from_path)


def shipping_desfiles_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "DTF Des Files"


def shipping_desfiles_processed_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "DTF Des Files - Processed"


def shipping_output_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Output"


def shipping_logs_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Logs"


def shipping_reports_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Reports"


def shipping_manual_print_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Manual Print Input"


def shipping_void_input_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Void Label Input"


def shipping_errors_dir(from_path: object | None = None) -> Path:
    return shipping_runtime_dir(from_path) / "Error and Failures"


def shipping_config_dir(from_path: object | None = None) -> Path:
    return shipping_app_dir(from_path)


def shipping_env_path(from_path: object | None = None) -> Path:
    return shipping_config_dir(from_path) / ".env"


def shipping_yaml_path(from_path: object | None = None) -> Path:
    return shipping_config_dir(from_path) / "shipping_config.yaml"

__all__ = [
    "shipping_app_dir",
    "shipping_database_dir",
    "shipping_runtime_dir",
    "shipping_desfiles_dir",
    "shipping_desfiles_processed_dir",
    "shipping_output_dir",
    "shipping_logs_dir",
    "shipping_reports_dir",
    "shipping_manual_print_dir",
    "shipping_void_input_dir",
    "shipping_errors_dir",
    "shipping_config_dir",
    "shipping_env_path",
    "shipping_yaml_path",
]
