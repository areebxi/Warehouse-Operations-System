"""Preflight stage 4: flag issues and optionally write the issues CSV."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from pipeline_split_by_process_item.merge_group_mask import (
    expand_issue_mask_to_merge_groups,
)

_WAREHOUSE = Path(__file__).resolve().parent.parent.parent.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared.demo_images import demo_image_lookup  # noqa: E402

from .config import NO_ISSUES
from .image_dry_run import flag_missing_images
from .service_types import PreflightResult, _fmt_secs, _is_blank, _yes_no


def flag_and_write_issues(
    df: pd.DataFrame,
    *,
    output_dir: Path,
    image_checks_enabled: bool,
    use_demo: bool,
    maps: dict[str, Any],
    log_callback: Callable[[str], None],
    t0: float,
) -> PreflightResult | object:
    """Return PreflightResult, NO_ISSUES."""
    log_callback("4/4  Checking issues…")
    t_chk = time.perf_counter()
    unmatched_flags = expand_issue_mask_to_merge_groups(
        df, df["Gender Apparel"].map(_is_blank)
    )

    if image_checks_enabled:
        with demo_image_lookup(use_demo):
            missing_logo_flags, missing_apparel_flags = flag_missing_images(
                df,
                apparel_stem_map=maps["apparel_map"],
                logo_normal_stem_map=maps["logo_normal_map"],
                logo_custom_stem_map=maps["logo_custom_map"],
                apparel_image_dir=maps["apparel_path"],
                logo_normal_dir=maps["logo_normal_path"],
                logo_custom_single_dir=maps["logo_custom_single_path"],
                logo_custom_double_dir=maps["logo_custom_double_path"],
            )
        missing_logo_flags = expand_issue_mask_to_merge_groups(df, missing_logo_flags)
    else:
        missing_logo_flags = pd.Series(False, index=df.index, dtype=bool)
        missing_apparel_flags = pd.Series(False, index=df.index, dtype=bool)

    df = df.copy()
    df["Unmatched SKU"] = unmatched_flags.map(_yes_no)
    df["Missing Logo"] = missing_logo_flags.map(_yes_no)
    df["Missing Apparel"] = missing_apparel_flags.map(_yes_no)

    issue_mask = unmatched_flags | missing_logo_flags | missing_apparel_flags
    issues = df.loc[issue_mask].copy()

    unmatched_count = int(unmatched_flags.sum())
    missing_logo_count = int(missing_logo_flags.sum())
    missing_apparel_count = int(missing_apparel_flags.sum())
    log_callback(f"      Done  [{_fmt_secs(time.perf_counter() - t_chk)}]")
    log_callback("")

    log_callback("Summary")
    log_callback(f"  Unmatched SKU     {unmatched_count:,}")
    log_callback(f"  Missing Logo      {missing_logo_count:,}")
    log_callback(f"  Missing Apparel   {missing_apparel_count:,}")
    log_callback(f"  Issue rows        {len(issues):,} / {len(df):,}")
    log_callback("")

    if issues.empty:
        log_callback(f"No preflight issues found.  (total {_fmt_secs(time.perf_counter() - t0)})")
        return NO_ISSUES

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    out_path = output_dir / f"Preflight Issues_{timestamp}.csv"
    issues.to_csv(out_path, index=False, encoding="utf-8")
    log_callback(f"Wrote {len(issues):,} issue row(s) →")
    log_callback(f"  {out_path}")
    log_callback(f"Finished in {_fmt_secs(time.perf_counter() - t0)}")
    return PreflightResult(
        path=out_path,
        unmatched_count=unmatched_count,
        missing_logo_count=missing_logo_count,
        missing_apparel_count=missing_apparel_count,
        issue_row_count=len(issues),
    )
