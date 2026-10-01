"""Build apparel/logo stem maps for preflight image dry-run."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Optional, Tuple

from pipeline_generate_packing_list_pdf.images import build_image_stem_map_impl

def build_preflight_stem_maps(
    apparel_dir: Optional[Path],
    logo_normal_dir: Optional[Path],
    logo_custom_single_dir: Optional[Path],
    logo_custom_double_dir: Optional[Path],
) -> Tuple[
    Optional[Dict[str, Path]],
    Optional[Dict[str, Path]],
    Optional[Dict[str, Path]],
    Optional[Path],
    Optional[Path],
    Optional[Path],
    Optional[Path],
]:
    """
    Index image folders like Step 8: apparel + normal top-level;
    custom single + double merged (first hit wins), also top-level.
    Returns (
        apparel_map, logo_normal_map, logo_custom_merged,
        apparel_dir, logo_normal_dir, logo_custom_single_dir, logo_custom_double_dir,
    ).
    """
    apparel_path = Path(apparel_dir) if apparel_dir else None
    logo_normal_path = Path(logo_normal_dir) if logo_normal_dir else None
    logo_custom_single_path = Path(logo_custom_single_dir) if logo_custom_single_dir else None
    logo_custom_double_path = Path(logo_custom_double_dir) if logo_custom_double_dir else None

    any_set = any(
        p is not None and str(p).strip()
        for p in (apparel_path, logo_normal_path, logo_custom_single_path, logo_custom_double_path)
    )
    if not any_set:
        return None, None, None, None, None, None, None

    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_apparel = executor.submit(build_image_stem_map_impl, apparel_path, recursive=False)
        fut_logo_custom_single = executor.submit(
            build_image_stem_map_impl, logo_custom_single_path, recursive=False
        )
        fut_logo_custom_double = executor.submit(
            build_image_stem_map_impl, logo_custom_double_path, recursive=False
        )
        fut_logo_normal = executor.submit(build_image_stem_map_impl, logo_normal_path, recursive=False)
        apparel_stem_map = fut_apparel.result()
        logo_custom_single_stem_map = fut_logo_custom_single.result()
        logo_custom_double_stem_map = fut_logo_custom_double.result()
        logo_normal_stem_map = fut_logo_normal.result()

    logo_custom_stem_map: Dict[str, Path] = {}
    for src in (logo_custom_single_stem_map, logo_custom_double_stem_map):
        if src:
            for stem, path in src.items():
                if stem not in logo_custom_stem_map:
                    logo_custom_stem_map[stem] = path

    return (
        apparel_stem_map or None,
        logo_normal_stem_map or None,
        logo_custom_stem_map or None,
        apparel_path if apparel_path and apparel_path.is_dir() else None,
        logo_normal_path if logo_normal_path and logo_normal_path.is_dir() else None,
        (
            logo_custom_single_path
            if logo_custom_single_path and logo_custom_single_path.is_dir()
            else None
        ),
        (
            logo_custom_double_path
            if logo_custom_double_path and logo_custom_double_path.is_dir()
            else None
        ),
    )
