"""Per-row missing logo / apparel dry-run using the same lookup rules as Step 8."""

from __future__ import annotations

from pipeline_preflight_issues.image_dry_run_chunk import _flag_chunk, _logo_design_tokens
from pipeline_preflight_issues.image_dry_run_flag import _IMAGE_CHUNK_SIZE, _IMAGE_MAX_WORKERS, _build_order_counts, _safe_str, flag_missing_images
from pipeline_preflight_issues.image_dry_run_index import _StemIndex, _iter_fallback_dirs, _make_find_exact, _make_find_prefix
from pipeline_preflight_issues.image_dry_run_maps import build_preflight_stem_maps

__all__ = [
    "_IMAGE_CHUNK_SIZE",
    "_IMAGE_MAX_WORKERS",
    "_StemIndex",
    "_build_order_counts",
    "_flag_chunk",
    "_iter_fallback_dirs",
    "_logo_design_tokens",
    "_make_find_exact",
    "_make_find_prefix",
    "_safe_str",
    "build_preflight_stem_maps",
    "flag_missing_images",
]
