from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pipeline_runtime.pipeline_log import PipelineLog


def _log_stem_sample_keys(
    log: Optional[PipelineLog],
    label: str,
    stem_map: Optional[Dict[str, Path]],
    limit: int = 40,
) -> None:
    if not log or not stem_map:
        return
    keys = sorted(stem_map.keys())[:limit]
    log.detail(
        f"  Step 8 stem sample ({label}): {len(keys)} of {len(stem_map)} key(s) (alphabetically first): {', '.join(keys)}"
    )
    if len(stem_map) > limit:
        log.detail(f"  Step 8 stem sample ({label}): ... {len(stem_map) - limit} more key(s) not listed")


def _log_overlay_sample(
    log: Optional[PipelineLog],
    position_code_to_draw: dict[str, str],
    limit: int = 50,
) -> None:
    if not log or not position_code_to_draw:
        return
    n = len(position_code_to_draw)
    take = min(limit, n)
    log.detail(f"  Step 8 workbook overlay (Position Code -> asset): {n} entr(y/ies); listing first {take}:")
    for k, v in sorted(position_code_to_draw.items(), key=lambda kv: str(kv[0]))[:take]:
        log.detail(f"    {k!r} -> {v}")
    if n > take:
        log.detail(f"  Step 8 workbook overlay: ... {n - take} more entr(y/ies) omitted")


def index_step8_stem_maps(
    *,
    apparel_dir,
    logo_custom_single_dir,
    logo_custom_double_dir,
    logo_normal_dir,
    workbook_path: Path,
    build_image_stem_map,
    load_position_code_to_draw,
    log: Optional[PipelineLog],
) -> dict[str, Any]:
    apparel_dir_path = Path(apparel_dir) if apparel_dir else None
    logo_custom_single_path = Path(logo_custom_single_dir) if logo_custom_single_dir else None
    logo_custom_double_path = Path(logo_custom_double_dir) if logo_custom_double_dir else None
    logo_normal_path = Path(logo_normal_dir) if logo_normal_dir else None

    t_index = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_apparel = executor.submit(build_image_stem_map, apparel_dir_path, recursive=False)
        fut_logo_custom_single = executor.submit(build_image_stem_map, logo_custom_single_path, recursive=False)
        fut_logo_custom_double = executor.submit(build_image_stem_map, logo_custom_double_path, recursive=False)
        fut_logo_normal = executor.submit(build_image_stem_map, logo_normal_path, recursive=False)
        apparel_stem_map = fut_apparel.result()
        logo_custom_single_stem_map = fut_logo_custom_single.result()
        logo_custom_double_stem_map = fut_logo_custom_double.result()
        logo_normal_stem_map = fut_logo_normal.result()
    index_elapsed = time.perf_counter() - t_index

    logo_custom_stem_map: Dict[str, Path] = {}
    for src in (logo_custom_single_stem_map, logo_custom_double_stem_map):
        if src:
            for stem, path in src.items():
                if stem not in logo_custom_stem_map:
                    logo_custom_stem_map[stem] = path

    run_timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    position_code_to_draw = load_position_code_to_draw(workbook_path) if workbook_path.exists() else {}
    has_image_lookup_main = (
        apparel_stem_map is not None
        or logo_custom_stem_map is not None
        or logo_normal_stem_map is not None
        or (apparel_dir_path and apparel_dir_path.is_dir())
        or (logo_custom_single_path and logo_custom_single_path.is_dir())
        or (logo_custom_double_path and logo_custom_double_path.is_dir())
        or (logo_normal_path and logo_normal_path.is_dir())
    )
    return {
        "apparel_dir_path": apparel_dir_path,
        "logo_custom_single_path": logo_custom_single_path,
        "logo_custom_double_path": logo_custom_double_path,
        "logo_normal_path": logo_normal_path,
        "apparel_stem_map": apparel_stem_map,
        "logo_custom_single_stem_map": logo_custom_single_stem_map,
        "logo_custom_double_stem_map": logo_custom_double_stem_map,
        "logo_normal_stem_map": logo_normal_stem_map,
        "logo_custom_stem_map": logo_custom_stem_map,
        "position_code_to_draw": position_code_to_draw,
        "run_timestamp": run_timestamp,
        "index_elapsed": index_elapsed,
        "has_image_lookup_main": has_image_lookup_main,
    }


def log_step8_index(log: Optional[PipelineLog], indexed: dict[str, Any]) -> None:
    if not log:
        return
    log.detail(
        f"Step 8/8: image folder index complete in {indexed['index_elapsed']:.2f}s — stem counts and paths:"
    )
    log.detail(
        "  Stem maps: scan each configured folder (top-level only, not recursive) for "
        ".png / .jpg / .jpeg; file stem -> path. PDF code resolves Apparel Image / Picture Name "
        "and Logo/Design Image tokens against these maps (custom vs normal rules in generator)."
    )
    la = len(indexed["apparel_stem_map"]) if indexed["apparel_stem_map"] else 0
    lcs = len(indexed["logo_custom_single_stem_map"]) if indexed["logo_custom_single_stem_map"] else 0
    lcd = len(indexed["logo_custom_double_stem_map"]) if indexed["logo_custom_double_stem_map"] else 0
    ln = len(indexed["logo_normal_stem_map"]) if indexed["logo_normal_stem_map"] else 0
    lc_merged = len(indexed["logo_custom_stem_map"]) if indexed["logo_custom_stem_map"] else 0
    log.detail(f"  Apparel dir: {indexed['apparel_dir_path'] or '(not set)'} -> {la} unique stem(s) indexed.")
    log.detail(f"  Logo custom single: {indexed['logo_custom_single_path'] or '(not set)'} -> {lcs} stem(s).")
    log.detail(
        f"  Logo custom double: {indexed['logo_custom_double_path'] or '(not set)'} -> {lcd} stem(s) "
        f"(merged with single -> {lc_merged} combined)."
    )
    log.detail(f"  Logo normal: {indexed['logo_normal_path'] or '(not set)'} -> {ln} stem(s).")
    log.detail(
        f"  Workbook overlay map (Position Code -> drawing): {len(indexed['position_code_to_draw'])} entr(y/ies)."
    )
    _log_overlay_sample(log, indexed["position_code_to_draw"])
    _log_stem_sample_keys(log, "apparel", indexed["apparel_stem_map"])
    _log_stem_sample_keys(log, "logo custom (merged single+double)", indexed["logo_custom_stem_map"])
    _log_stem_sample_keys(log, "logo normal", indexed["logo_normal_stem_map"])
    log.detail(
        "  Step 8: full image trace (context + every row + summary) is written into this same "
        "pipeline transcript below — no second file under logs/."
    )
