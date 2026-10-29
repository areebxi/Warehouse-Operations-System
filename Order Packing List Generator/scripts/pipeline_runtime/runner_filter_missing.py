"""Step 5→6 missing logo/apparel filter + sideline move helpers."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from pipeline_runtime.filter_missing_logos import filter_step6_csvs_for_missing_logos
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import (
    _move_missing_apparel_to_root,
    _move_missing_logo_to_root,
)
from shared.demo_images import demo_image_lookup


def filter_and_move_missing_images(
    *,
    step5_path: Path,
    output_root: Path,
    token: str,
    logo_custom_single_dir,
    logo_custom_double_dir,
    logo_normal_dir,
    apparel_dir,
    use_demo: bool,
    date_dd_mm_yyyy: str,
    shift_label: str,
    log: Optional[PipelineLog],
    lc,
) -> tuple[object, Optional[Path], Optional[Path]]:
    if log:
        log.step("Filtering missing logos/apparels (before process/item naming)...")
    t_miss = time.perf_counter()
    with demo_image_lookup(use_demo):
        (
            kept_step5,
            missing_logo_path,
            missing_apparel_path,
            missing_image_count,
        ) = filter_step6_csvs_for_missing_logos(
            [step5_path],
            output_root=output_root,
            token=token,
            logo_custom_single_dir=logo_custom_single_dir,
            logo_custom_double_dir=logo_custom_double_dir,
            logo_normal_dir=logo_normal_dir,
            apparel_dir=apparel_dir,
            log=lc,
        )
    if missing_logo_path is not None:
        moved = _move_missing_logo_to_root(
            missing_logo_path, date_dd_mm_yyyy, shift_label
        )
        if moved is not None:
            missing_logo_path = moved
    if missing_apparel_path is not None:
        moved = _move_missing_apparel_to_root(
            missing_apparel_path, date_dd_mm_yyyy, shift_label
        )
        if moved is not None:
            missing_apparel_path = moved
    if log:
        parts = [f"excluded {missing_image_count} row(s)"]
        if missing_logo_path:
            parts.append(f"logo: {missing_logo_path}")
        if missing_apparel_path:
            parts.append(f"apparel: {missing_apparel_path}")
        log.detail(
            "  Missing-image filter done — "
            + "; ".join(parts)
            + f"  [{time.perf_counter() - t_miss:.2f}s]"
        )
    return kept_step5, missing_logo_path, missing_apparel_path
