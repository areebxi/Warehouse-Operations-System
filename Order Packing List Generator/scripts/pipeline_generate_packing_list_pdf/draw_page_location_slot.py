"""Customise LOCATION image slot helpers for the packing PDF logo grid."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from pipeline_generate_packing_list_pdf.back_print_hint import LOCATION_LABEL


def _paths_equal(left: Optional[Path], right: Optional[Path]) -> bool:
    if left is None or right is None:
        return False
    try:
        return Path(left).resolve() == Path(right).resolve()
    except OSError:
        return Path(left) == Path(right)


def lookup_location_path(
    *,
    base_name: str,
    item_sku: str,
    is_scoped: bool,
    logo_customise_dir: Optional[Path],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    find_image_custom_exact: Callable[..., Optional[Path]],
    find_image_custom_fbpi: Callable[..., Optional[Path]],
) -> Optional[Path]:
    """Return ``{order}-LOCATION`` (optional ``-{sku}``) when that file exists."""
    candidates: List[str] = []
    if is_scoped and item_sku:
        candidates.append(f"{base_name}-{LOCATION_LABEL}-{item_sku}")
    candidates.append(f"{base_name}-{LOCATION_LABEL}")
    for candidate in candidates:
        found = find_image_custom_exact(
            logo_customise_dir, candidate, logo_custom_stem_map, recursive=True
        )
        if found is not None:
            return found
    if not is_scoped:
        return find_image_custom_fbpi(
            logo_custom_stem_map, f"{base_name}-{LOCATION_LABEL}"
        )
    return None


def append_location_slot(
    fbpi_slots: List[Tuple[Path, str]],
    location_path: Optional[Path],
    base_custom_path: Optional[Path],
) -> Tuple[List[Tuple[Path, str]], Optional[Path]]:
    """Add LOCATION to the design grid without duplicating an already-used file.

    Extra F/B/P/S images occupy at most four grid cells after the base image.
    If those four are full and there is no base image, LOCATION uses slot 0.
    """
    if location_path is None:
        return fbpi_slots, base_custom_path
    already = _paths_equal(base_custom_path, location_path) or any(
        _paths_equal(path, location_path) for path, _label in fbpi_slots
    )
    if already:
        return fbpi_slots, base_custom_path
    if len(fbpi_slots) < 4:
        fbpi_slots.append((location_path, LOCATION_LABEL))
        return fbpi_slots, base_custom_path
    if base_custom_path is None:
        return fbpi_slots, location_path
    return fbpi_slots, base_custom_path
