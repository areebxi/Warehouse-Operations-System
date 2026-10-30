"""After Step 5, before Step 6 naming: drop missing-logo rows; report missing apparel."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_preflight_issues.image_dry_run import (
    build_preflight_stem_maps,
    flag_missing_images,
)
from pipeline_runtime.filter_missing_images_io import write_sideline_csv
from pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from pipeline_split_by_process_item.duplicate_order_suffixes import (
    assign_merge_order_number_suffixes,
)
from pipeline_split_by_process_item.grouping_quantity import _expand_df_by_quantity
from pipeline_split_by_process_item.merge_group_mask import (
    expand_issue_mask_to_merge_groups,
)

_ORIG_IDX = "_filter_orig_idx"


def _lookup_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Expand qty and apply custom stems so image lookup matches Step 6/PDF."""
    work = df.copy()
    work[_ORIG_IDX] = range(len(work))
    work = _expand_df_by_quantity(work)
    return assign_merge_order_number_suffixes(work)


def filter_step6_csvs_for_missing_logos(
    step6_csvs: list[Path],
    *,
    output_root: Path,
    token: str,
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    apparel_dir: Optional[str | Path] = None,
    log: Optional[Callable[[str], None]] = None,
) -> tuple[list[Path], Optional[Path], Optional[Path], int]:
    """
    Dry-run logo/apparel lookup on each CSV (Step 5 before naming). Exclude
    missing-logo rows and merge siblings; missing apparel is reported only
    (rows still pack). Writes ``missing_logo_orders_{token}.csv`` (holding)
    and ``missing_apparel_orders_{token}.csv`` (report) when non-empty.

    Returns (kept_csvs, missing_logo_csv_or_none, missing_apparel_csv_or_none,
    excluded_row_count). Skips when neither logo nor apparel folders are set.
    """
    def _emit(msg: str) -> None:
        if log:
            log(msg)

    (
        apparel_map,
        logo_normal_map,
        logo_custom_map,
        apparel_path,
        logo_normal_path,
        logo_custom_single_path,
        logo_custom_double_path,
    ) = build_preflight_stem_maps(
        Path(apparel_dir) if apparel_dir else None,
        Path(logo_normal_dir) if logo_normal_dir else None,
        Path(logo_custom_single_dir) if logo_custom_single_dir else None,
        Path(logo_custom_double_dir) if logo_custom_double_dir else None,
    )
    has_logo = logo_normal_map is not None or logo_custom_map is not None or (
        logo_normal_path is not None and logo_normal_path.is_dir()
    ) or (
        logo_custom_single_path is not None and logo_custom_single_path.is_dir()
    ) or (
        logo_custom_double_path is not None and logo_custom_double_path.is_dir()
    )
    has_apparel = apparel_map is not None or (
        apparel_path is not None and apparel_path.is_dir()
    )
    if not has_logo and not has_apparel:
        _emit("  Missing-image filter: skipped (no logo/apparel folders set).")
        return step6_csvs, None, None, 0

    logo_frames: list[pd.DataFrame] = []
    apparel_frames: list[pd.DataFrame] = []
    kept_csvs: list[Path] = []
    total_excluded = 0
    logo_siblings = 0
    apparel_siblings = 0

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

        df = df.reset_index(drop=True)
        work = _lookup_frame(df)
        missing_logo_flags, missing_apparel_flags = flag_missing_images(
            work,
            apparel_stem_map=apparel_map if has_apparel else None,
            logo_normal_stem_map=logo_normal_map if has_logo else None,
            logo_custom_stem_map=logo_custom_map if has_logo else None,
            apparel_image_dir=apparel_path if has_apparel else None,
            logo_normal_dir=logo_normal_path if has_logo else None,
            logo_custom_single_dir=logo_custom_single_path if has_logo else None,
            logo_custom_double_dir=logo_custom_double_path if has_logo else None,
        )
        logo_ex = expand_issue_mask_to_merge_groups(work, missing_logo_flags)
        apparel_ex = expand_issue_mask_to_merge_groups(work, missing_apparel_flags)
        exclude_work = logo_ex  # apparel reports only; packing continues
        n_exclude = int(exclude_work.sum())
        raw_logo = int(missing_logo_flags.sum())
        raw_apparel = int(missing_apparel_flags.sum())
        logo_siblings += max(0, int(logo_ex.sum()) - raw_logo)
        apparel_siblings += max(0, int(apparel_ex.sum()) - raw_apparel)
        drop_cols = [c for c in (_ORIG_IDX,) if c in work.columns]
        if int(logo_ex.sum()):
            logo_frames.append(work.loc[logo_ex].drop(columns=drop_cols, errors="ignore"))
        if int(apparel_ex.sum()):
            apparel_frames.append(
                work.loc[apparel_ex].drop(columns=drop_cols, errors="ignore")
            )
        if n_exclude:
            dropped = set(int(v) for v in work.loc[exclude_work, _ORIG_IDX].tolist())
            total_excluded += n_exclude
            keep_mask = [i not in dropped for i in range(len(df))]
            kept = df.loc[keep_mask].copy()
            if kept.empty:
                try:
                    csv_path.unlink()
                except OSError:
                    pass
                _emit(
                    f"  Missing-image filter: {csv_path.name} — excluded all "
                    f"{n_exclude} missing-logo row(s); file removed."
                )
            else:
                kept.to_csv(csv_path, index=False, encoding="utf-8")
                kept_csvs.append(csv_path)
                _emit(
                    f"  Missing-image filter: {csv_path.name} — excluded {n_exclude} "
                    f"missing-logo row(s), kept {len(kept)}."
                )
        else:
            kept_csvs.append(csv_path)
            if raw_apparel:
                _emit(
                    f"  Missing-image filter: {csv_path.name} — "
                    f"{raw_apparel} missing-apparel row(s) reported; packing continues."
                )

    missing_logo_path = write_sideline_csv(
        logo_frames,
        output_root,
        f"missing_logo_orders_{token}.csv",
        label="Missing-logo filter",
        sibling_pullins=logo_siblings,
        log=log,
    )
    missing_apparel_path = write_sideline_csv(
        apparel_frames,
        output_root,
        f"missing_apparel_orders_{token}.csv",
        label="Missing-apparel filter",
        sibling_pullins=apparel_siblings,
        log=log,
    )
    return kept_csvs, missing_logo_path, missing_apparel_path, total_excluded
