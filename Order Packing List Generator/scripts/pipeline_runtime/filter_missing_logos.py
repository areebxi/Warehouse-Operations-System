"""Post-Step 6: exclude rows (and merge siblings) with missing logo files."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_preflight_issues.image_dry_run import (
    build_preflight_stem_maps,
    flag_missing_images,
)
from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from scripts.pipeline_split_by_process_item.merge_group_mask import (
    expand_issue_mask_to_merge_groups,
)


def filter_step6_csvs_for_missing_logos(
    step6_csvs: list[Path],
    *,
    output_root: Path,
    token: str,
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    log: Optional[Callable[[str], None]] = None,
) -> tuple[list[Path], Optional[Path], int]:
    """
    Dry-run logo lookup on each Step-6 process CSV; exclude missing-logo rows
    and their merge siblings. Writes ``missing_logo_orders_{token}.csv`` when any.

    Returns (kept_csvs, missing_logo_csv_or_none, excluded_row_count).
    When no logo folders are configured, returns step6_csvs unchanged.
    """
    def _emit(msg: str) -> None:
        if log:
            log(msg)

    (
        _,
        logo_normal_map,
        logo_custom_map,
        _,
        logo_normal_path,
        logo_custom_single_path,
        logo_custom_double_path,
    ) = build_preflight_stem_maps(
        None,
        Path(logo_normal_dir) if logo_normal_dir else None,
        Path(logo_custom_single_dir) if logo_custom_single_dir else None,
        Path(logo_custom_double_dir) if logo_custom_double_dir else None,
    )
    has_logo_lookup = logo_normal_map is not None or logo_custom_map is not None or (
        logo_normal_path is not None and logo_normal_path.is_dir()
    ) or (
        logo_custom_single_path is not None and logo_custom_single_path.is_dir()
    ) or (
        logo_custom_double_path is not None and logo_custom_double_path.is_dir()
    )
    if not has_logo_lookup:
        _emit("  Missing-logo filter: skipped (no logo folders set).")
        return step6_csvs, None, 0

    excluded_frames: list[pd.DataFrame] = []
    kept_csvs: list[Path] = []
    total_excluded = 0
    sibling_pullins = 0

    for csv_path in step6_csvs:
        if not csv_path.exists():
            continue
        df = read_csv_with_order_numbers(csv_path)
        if df.empty:
            try:
                csv_path.unlink()
            except OSError:
                pass
            continue

        missing_logo_flags, _ = flag_missing_images(
            df,
            apparel_stem_map=None,
            logo_normal_stem_map=logo_normal_map,
            logo_custom_stem_map=logo_custom_map,
            apparel_image_dir=None,
            logo_normal_dir=logo_normal_path,
            logo_custom_single_dir=logo_custom_single_path,
            logo_custom_double_dir=logo_custom_double_path,
        )
        raw_missing = int(missing_logo_flags.sum())
        exclude_mask = expand_issue_mask_to_merge_groups(df, missing_logo_flags)
        n_exclude = int(exclude_mask.sum())
        if n_exclude:
            sibling_pullins += max(0, n_exclude - raw_missing)
            excluded_frames.append(df.loc[exclude_mask].copy())
            total_excluded += n_exclude
            kept = df.loc[~exclude_mask].copy()
            if kept.empty:
                try:
                    csv_path.unlink()
                except OSError:
                    pass
                _emit(
                    f"  Missing-logo filter: {csv_path.name} — excluded all {n_exclude} row(s); file removed."
                )
            else:
                kept.to_csv(csv_path, index=False, encoding="utf-8")
                kept_csvs.append(csv_path)
                _emit(
                    f"  Missing-logo filter: {csv_path.name} — excluded {n_exclude} row(s), "
                    f"kept {len(kept)}."
                )
        else:
            kept_csvs.append(csv_path)

    missing_path: Optional[Path] = None
    if excluded_frames:
        combined = pd.concat(excluded_frames, ignore_index=True, sort=False)
        missing_path = output_root / f"missing_logo_orders_{token}.csv"
        combined.to_csv(missing_path, index=False, encoding="utf-8")
        _emit(
            f"  Missing-logo filter: wrote {len(combined)} row(s) -> {missing_path.name}"
            + (f" ({sibling_pullins} merge-sibling pull-in(s))" if sibling_pullins else "")
            + "."
        )
    else:
        _emit("  Missing-logo filter: no missing logos.")

    return kept_csvs, missing_path, total_excluded
