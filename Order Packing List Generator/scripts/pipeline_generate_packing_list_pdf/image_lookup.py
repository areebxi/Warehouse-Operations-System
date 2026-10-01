"""Filesystem image path lookup (stem maps, apparel/logo resolution)."""

from __future__ import annotations

from pipeline_generate_packing_list_pdf.image_lookup_custom import find_image_custom_exact_impl, find_image_custom_fbpi_impl, find_image_custom_logo_impl
from pipeline_generate_packing_list_pdf.image_lookup_find import find_image_impl
from pipeline_generate_packing_list_pdf.image_lookup_logo import find_image_normal_logo_impl
from pipeline_generate_packing_list_pdf.image_lookup_stem import _IMAGE_EXTS, _count_image_files, _demo_fallback, _path_if_file, _remember_stem, _scan_image_stem_map, build_image_stem_map_impl, clear_stem_map_caches, find_image_in_dir_impl, probe_exact_image_impl

__all__ = [
    "_IMAGE_EXTS",
    "_count_image_files",
    "_demo_fallback",
    "_path_if_file",
    "_remember_stem",
    "_scan_image_stem_map",
    "build_image_stem_map_impl",
    "clear_stem_map_caches",
    "find_image_custom_exact_impl",
    "find_image_custom_fbpi_impl",
    "find_image_custom_logo_impl",
    "find_image_impl",
    "find_image_in_dir_impl",
    "find_image_normal_logo_impl",
    "probe_exact_image_impl",
]
