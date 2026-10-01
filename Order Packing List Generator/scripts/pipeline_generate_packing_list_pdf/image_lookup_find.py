"""Exact stem image find helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from pipeline_generate_packing_list_pdf.image_lookup_stem import (
    _demo_fallback,
    _path_if_file,
    _remember_stem,
    find_image_in_dir_impl,
    probe_exact_image_impl,
)

def find_image_impl(
    root_dir: Optional[Path],
    base_name: str,
    stem_map: Optional[Dict[str, Path]],
    *,
    recursive: bool = False,
) -> Optional[Path]:
    """Return Path for base_name in root_dir, using stem_map if provided else directory search (recursive or top-level only)."""
    if not base_name:
        return None
    if stem_map is not None:
        found = _path_if_file(stem_map.get(base_name))
        if found is not None:
            return found
        # Case-insensitive fallback (e.g. "Only-Design-Iron-On-Sticker" vs "only-design-iron-on-sticker")
        lower = base_name.lower()
        for stem, path in stem_map.items():
            if stem.lower() == lower:
                found = _path_if_file(path)
                if found is not None:
                    return found
        # Map miss: cheap exact probe only (never full-scan huge Drive folders).
        live = probe_exact_image_impl(root_dir, base_name)
        if live is not None:
            return _remember_stem(stem_map, live.stem, live)
        fb = _demo_fallback("apparel", base_name)
        if fb is not None:
            return fb
        return None
    if not root_dir or not root_dir.is_dir():
        fb = _demo_fallback("apparel", base_name)
        return fb
    result = find_image_in_dir_impl(root_dir, base_name, recursive=recursive)
    if result is not None:
        return result
    return _demo_fallback("apparel", base_name)
