"""Flag missing logo/apparel rows for preflight dry-run."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from pipeline_generate_packing_list_pdf.core_helpers import safe_str_impl
from pipeline_generate_packing_list_pdf.images import (
    find_image_custom_fbpi_impl,
    find_image_custom_logo_impl,
    find_image_normal_logo_impl,
)
from pipeline_generate_packing_list_pdf.image_lookup import probe_exact_image_impl
from shared.demo_images import demo_fallback_path
from pipeline_generate_packing_list_pdf.reporting import build_order_counts_impl
from pipeline_preflight_issues.image_dry_run_index import (
    _StemIndex,
    _iter_fallback_dirs,
    _make_find_exact,
    _make_find_prefix,
)
from pipeline_preflight_issues.image_dry_run_chunk import _flag_chunk

_safe_str = safe_str_impl
_build_order_counts = partial(build_order_counts_impl, safe_str=_safe_str)

_IMAGE_CHUNK_SIZE = 250
_IMAGE_MAX_WORKERS = 4

def flag_missing_images(
    df: pd.DataFrame,
    *,
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    apparel_image_dir: Optional[Path],
    logo_normal_dir: Optional[Path],
    logo_custom_single_dir: Optional[Path] = None,
    logo_custom_double_dir: Optional[Path] = None,
) -> tuple[pd.Series, pd.Series]:
    """
    Return (missing_logo, missing_apparel) boolean Series aligned to df.index.
    Mirrors count_image_lookup_stats_impl found/not-found rules.
    When no lookup dirs/maps are available, both series are False.
    """
    missing_logo = pd.Series(False, index=df.index, dtype=bool)
    missing_apparel = pd.Series(False, index=df.index, dtype=bool)

    has_apparel_lookup = apparel_stem_map is not None or (
        apparel_image_dir is not None and apparel_image_dir.is_dir()
    )
    has_logo_lookup = (
        logo_normal_stem_map is not None
        or logo_custom_stem_map is not None
        or (logo_normal_dir is not None and logo_normal_dir.is_dir())
        or (logo_custom_single_dir is not None and logo_custom_single_dir.is_dir())
        or (logo_custom_double_dir is not None and logo_custom_double_dir.is_dir())
    )
    if not has_apparel_lookup and not has_logo_lookup:
        return missing_logo, missing_apparel

    apparel_index = _StemIndex(apparel_stem_map) if apparel_stem_map else None
    normal_index = _StemIndex(logo_normal_stem_map) if logo_normal_stem_map else None
    custom_index = _StemIndex(logo_custom_stem_map) if logo_custom_stem_map else None

    find_apparel = _make_find_exact(apparel_index, [apparel_image_dir], demo_kind="apparel")
    find_normal = _make_find_prefix(
        normal_index, find_image_normal_logo_impl, [logo_normal_dir], demo_kind="normal"
    )
    find_custom_exact = _make_find_exact(
        custom_index, [logo_custom_single_dir, logo_custom_double_dir], demo_kind="custom"
    )
    find_custom_logo = _make_find_prefix(
        custom_index,
        find_image_custom_logo_impl,
        [logo_custom_single_dir, logo_custom_double_dir],
        demo_kind="custom",
    )

    def find_custom_fbpi(stem_map, candidate_stem):
        if custom_index is not None:
            found = custom_index.find_prefix(candidate_stem)
            if found is not None:
                return found
            for directory in _iter_fallback_dirs(
                None, [logo_custom_single_dir, logo_custom_double_dir]
            ):
                live = probe_exact_image_impl(directory, candidate_stem)
                if live is not None:
                    return custom_index.remember(live.stem, live)
            return demo_fallback_path("custom", candidate_stem)
        return find_image_custom_fbpi_impl(stem_map, candidate_stem)

    order_number_counts = _build_order_counts(df)
    n = len(df)
    if n == 0:
        return missing_logo, missing_apparel

    chunk_size = max(_IMAGE_CHUNK_SIZE, (n + _IMAGE_MAX_WORKERS - 1) // max(_IMAGE_MAX_WORKERS, 1))
    chunks = [df.iloc[i : i + chunk_size] for i in range(0, n, chunk_size)]

    common_kwargs = dict(
        has_apparel_lookup=has_apparel_lookup,
        has_logo_lookup=has_logo_lookup,
        order_number_counts=order_number_counts,
        apparel_image_dir=apparel_image_dir,
        apparel_stem_map=apparel_stem_map,
        logo_normal_dir=logo_normal_dir,
        logo_normal_stem_map=logo_normal_stem_map,
        logo_custom_stem_map=logo_custom_stem_map,
        find_apparel=find_apparel,
        find_normal=find_normal,
        find_custom_exact=find_custom_exact,
        find_custom_logo=find_custom_logo,
        find_custom_fbpi=find_custom_fbpi,
    )

    if len(chunks) == 1:
        logo_idxs, apparel_idxs = _flag_chunk(chunks[0], **common_kwargs)
        if logo_idxs:
            missing_logo.loc[logo_idxs] = True
        if apparel_idxs:
            missing_apparel.loc[apparel_idxs] = True
        return missing_logo, missing_apparel

    with ThreadPoolExecutor(max_workers=min(_IMAGE_MAX_WORKERS, len(chunks))) as executor:
        futures = [executor.submit(_flag_chunk, chunk, **common_kwargs) for chunk in chunks]
        for fut in as_completed(futures):
            logo_idxs, apparel_idxs = fut.result()
            if logo_idxs:
                missing_logo.loc[logo_idxs] = True
            if apparel_idxs:
                missing_apparel.loc[apparel_idxs] = True

    return missing_logo, missing_apparel
