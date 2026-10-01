"""Preflight stage 1: resolve image dirs and build stem maps."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

_WAREHOUSE = Path(__file__).resolve().parent.parent.parent.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared.demo_images import demo_image_lookup, effective_image_dirs  # noqa: E402

from .image_dry_run import build_preflight_stem_maps
from .service_types import _fmt_secs


def index_image_folders(
    log_callback: Callable[[str], None],
    *,
    use_demo_images: bool,
    apparel_dir: Optional[Path],
    logo_normal_dir: Optional[Path],
    logo_custom_single_dir: Optional[Path],
    logo_custom_double_dir: Optional[Path],
) -> tuple[bool, bool, dict[str, Any]]:
    """
    Return (image_checks_enabled, use_demo, maps).
    maps keys: apparel_map, logo_normal_map, logo_custom_map,
    apparel_path, logo_normal_path, logo_custom_single_path, logo_custom_double_path.
    """
    log_callback("1/4  Indexing image folders…")
    t_img = time.perf_counter()
    use_demo = bool(use_demo_images)
    (
        resolved_apparel,
        resolved_normal,
        resolved_custom_single,
        resolved_custom_double,
    ) = effective_image_dirs(
        use_demo,
        apparel_dir,
        logo_normal_dir,
        logo_custom_single_dir,
        logo_custom_double_dir,
    )
    if use_demo:
        log_callback("      Demo images enabled (Demo Images Database/)")
    with demo_image_lookup(use_demo):
        (
            apparel_map,
            logo_normal_map,
            logo_custom_map,
            apparel_path,
            logo_normal_path,
            logo_custom_single_path,
            logo_custom_double_path,
        ) = build_preflight_stem_maps(
            resolved_apparel,
            resolved_normal,
            resolved_custom_single,
            resolved_custom_double,
        )
    image_checks_enabled = (
        use_demo
        or apparel_map is not None
        or logo_normal_map is not None
        or logo_custom_map is not None
        or apparel_path is not None
        or logo_normal_path is not None
        or logo_custom_single_path is not None
        or logo_custom_double_path is not None
    )
    if not image_checks_enabled:
        log_callback(
            f"      Skipped (no folders set) — Unmatched SKU only  [{_fmt_secs(time.perf_counter() - t_img)}]"
        )
    else:
        la = len(apparel_map) if apparel_map else 0
        ln = len(logo_normal_map) if logo_normal_map else 0
        lc = len(logo_custom_map) if logo_custom_map else 0
        log_callback(
            f"      Done — apparel {la:,} · normal logos {ln:,} · custom logos {lc:,}"
            f"  [{_fmt_secs(time.perf_counter() - t_img)}]"
        )
    maps = {
        "apparel_map": apparel_map,
        "logo_normal_map": logo_normal_map,
        "logo_custom_map": logo_custom_map,
        "apparel_path": apparel_path,
        "logo_normal_path": logo_normal_path,
        "logo_custom_single_path": logo_custom_single_path,
        "logo_custom_double_path": logo_custom_double_path,
    }
    return image_checks_enabled, use_demo, maps
