"""
I/O and external resources (files, archives, databases).

This package re-exports legacy flat modules from `src/` to enable modular
imports without changing runtime behavior.
"""

from .file_handlers import (
    load_color_bar_from_app_dir,
    load_configuration_workbook,
    load_pocket_design_ids_database,
    load_print_size_overrides,
    load_size_reference_from_app_dir,
)

from .rar_utils import (
    create_rar_from_pngs,
    generate_rar_name,
    copy_rar_to_dtf_queues,
)

__all__ = [
    "load_color_bar_from_app_dir",
    "load_configuration_workbook",
    "load_pocket_design_ids_database",
    "load_print_size_overrides",
    "load_size_reference_from_app_dir",
    "create_rar_from_pngs",
    "generate_rar_name",
    "copy_rar_to_dtf_queues",
]

