"""Per-row missing logo / apparel dry-run using the same lookup rules as Step 8."""

from __future__ import annotations

import bisect
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.core_helpers import (
    is_plain_order_sku_impl,
    logo_design_tokens_impl,
    safe_str_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_custom_logo_context import (
    resolve_custom_logo_context_impl,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_logo_lookup import (
    logo_image_for_slot_impl,
)
from scripts.pipeline_generate_packing_list_pdf.images import (
    build_image_stem_map_impl,
    find_image_custom_exact_impl,
    find_image_custom_fbpi_impl,
    find_image_custom_logo_impl,
    find_image_impl,
    find_image_normal_logo_impl,
)
from scripts.pipeline_generate_packing_list_pdf.image_lookup import probe_exact_image_impl
from scripts.pipeline_generate_packing_list_pdf.reporting import build_order_counts_impl

_safe_str = safe_str_impl
_logo_design_tokens = partial(logo_design_tokens_impl, safe_str=_safe_str)
_build_order_counts = partial(build_order_counts_impl, safe_str=_safe_str)

# Row chunks for parallel image dry-run (GIL-friendly work with dict lookups).
_IMAGE_CHUNK_SIZE = 250
_IMAGE_MAX_WORKERS = 4


class _StemIndex:
    """Exact + casefold + sorted-prefix indexes over an image stem map."""

    __slots__ = ("exact", "lower", "sorted_stems", "sorted_lower", "lower_to_path")

    def __init__(self, stem_map: Optional[Dict[str, Path]]) -> None:
        self.exact: Dict[str, Path] = stem_map or {}
        self.lower: Dict[str, Path] = {}
        self.lower_to_path: Dict[str, Path] = {}
        for stem, path in self.exact.items():
            low = stem.lower()
            self.lower.setdefault(low, path)
            self.lower_to_path.setdefault(low, path)
        self.sorted_stems = sorted(self.exact.keys())
        self.sorted_lower = sorted(self.lower.keys())

    @staticmethod
    def _existing(path: Optional[Path]) -> Optional[Path]:
        if path is None:
            return None
        try:
            p = Path(path)
            return p if p.is_file() else None
        except OSError:
            return None

    def remember(self, stem: str, path: Path) -> Path:
        already = stem in self.exact
        self.exact[stem] = path
        low = stem.lower()
        self.lower[low] = path
        self.lower_to_path[low] = path
        if not already:
            bisect.insort(self.sorted_stems, stem)
        if low not in self.sorted_lower:
            bisect.insort(self.sorted_lower, low)
        return path

    def find_exact(self, name: str) -> Optional[Path]:
        if not name:
            return None
        found = self._existing(self.exact.get(name))
        if found is not None:
            return found
        return self._existing(self.lower.get(name.lower()))

    def find_prefix(self, token: str) -> Optional[Path]:
        """First stem that starts with token (case-sensitive, then casefold)."""
        if not token:
            return None
        exact = self._existing(self.exact.get(token))
        if exact is not None:
            return exact
        i = bisect.bisect_left(self.sorted_stems, token)
        if i < len(self.sorted_stems) and self.sorted_stems[i].startswith(token):
            found = self._existing(self.exact.get(self.sorted_stems[i]))
            if found is not None:
                return found
        token_lower = token.lower()
        j = bisect.bisect_left(self.sorted_lower, token_lower)
        if j < len(self.sorted_lower) and self.sorted_lower[j].startswith(token_lower):
            return self._existing(self.lower_to_path.get(self.sorted_lower[j]))
        return None


def _iter_fallback_dirs(
    root_dir: Optional[Path], fallback_dirs: Optional[List[Optional[Path]]]
) -> List[Path]:
    out: List[Path] = []
    for raw in (root_dir, *(fallback_dirs or ())):
        if raw is None:
            continue
        path = Path(raw)
        if path.is_dir() and path not in out:
            out.append(path)
    return out


def _make_find_exact(
    index: Optional[_StemIndex],
    fallback_dirs: Optional[List[Optional[Path]]] = None,
):
    def _find(root_dir, base_name, stem_map, *, recursive: bool = False):
        if index is not None:
            found = index.find_exact(base_name)
            if found is not None:
                return found
            # Index miss: O(1) exact filename probe only (no Drive-wide glob).
            for directory in _iter_fallback_dirs(root_dir, fallback_dirs):
                live = probe_exact_image_impl(directory, base_name)
                if live is not None:
                    return index.remember(live.stem, live)
            return None
        return find_image_impl(root_dir, base_name, stem_map, recursive=recursive)

    return _find


def _make_find_prefix(
    index: Optional[_StemIndex],
    fallback_fn,
    fallback_dirs: Optional[List[Optional[Path]]] = None,
):
    def _find(root_dir, token, stem_map, *, recursive: bool = False):
        if index is not None:
            found = index.find_prefix(token)
            if found is not None:
                return found
            for directory in _iter_fallback_dirs(root_dir, fallback_dirs):
                live = probe_exact_image_impl(directory, token)
                if live is not None:
                    return index.remember(live.stem, live)
            return None
        return fallback_fn(root_dir, token, stem_map, recursive=recursive)

    return _find


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


def _flag_chunk(
    df_chunk: pd.DataFrame,
    *,
    has_apparel_lookup: bool,
    has_logo_lookup: bool,
    order_number_counts: dict,
    apparel_image_dir: Optional[Path],
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_normal_dir: Optional[Path],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    find_apparel,
    find_normal,
    find_custom_exact,
    find_custom_logo,
    find_custom_fbpi,
) -> Tuple[List[object], List[object]]:
    missing_logo_idxs: List[object] = []
    missing_apparel_idxs: List[object] = []
    logo_customise_dir = None

    for i in range(len(df_chunk)):
        row = df_chunk.iloc[i]
        idx = df_chunk.index[i]
        if has_apparel_lookup:
            apparel_text = _safe_str(row.get("Apparel Image", ""))
            picture_name = _safe_str(row.get("Picture Name", ""))
            if apparel_text or picture_name:
                found = False
                for name in (apparel_text, picture_name):
                    if not name:
                        continue
                    if find_apparel(apparel_image_dir, name, apparel_stem_map, recursive=False):
                        found = True
                        break
                if not found:
                    missing_apparel_idxs.append(idx)

        if not has_logo_lookup:
            continue
        tokens = _logo_design_tokens(row.get("Logo/Design Image"))
        if not tokens:
            continue
        is_customised = _safe_str(row.get("Customise", "")).lower() == "yes"
        item_sku_raw = _safe_str(row.get("Item SKU", ""))
        if is_plain_order_sku_impl(item_sku_raw):
            continue
        if is_customised:
            _ic, is_scoped, base_custom_path, fbpi_slots = resolve_custom_logo_context_impl(
                row,
                order_number_counts,
                is_plain_order=False,
                logo_customise_dir=logo_customise_dir,
                logo_custom_stem_map=logo_custom_stem_map,
                safe_str=_safe_str,
                logo_design_tokens=_logo_design_tokens,
                find_image_custom_exact=find_custom_exact,
                find_image_custom_logo=find_custom_logo,
                find_image_custom_fbpi=find_custom_fbpi,
            )
            p0 = logo_image_for_slot_impl(
                0,
                row,
                fbpi_slots=fbpi_slots,
                base_custom_path=base_custom_path,
                is_scoped_custom_merge=is_scoped,
                logo_customise_dir=logo_customise_dir,
                logo_custom_stem_map=logo_custom_stem_map,
                logo_normal_dir=logo_normal_dir,
                logo_normal_stem_map=logo_normal_stem_map,
                safe_str=_safe_str,
                logo_design_tokens=_logo_design_tokens,
                find_image_custom_exact=find_custom_exact,
                find_image_custom_logo=find_custom_logo,
                find_image_normal_logo=find_normal,
            )
            if p0 is None:
                missing_logo_idxs.append(idx)
        else:
            all_ok = True
            for tok in tokens:
                if not find_normal(logo_normal_dir, tok, logo_normal_stem_map, recursive=False):
                    all_ok = False
                    break
            if not all_ok:
                missing_logo_idxs.append(idx)

    return missing_logo_idxs, missing_apparel_idxs


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

    find_apparel = _make_find_exact(apparel_index, [apparel_image_dir])
    find_normal = _make_find_prefix(
        normal_index, find_image_normal_logo_impl, [logo_normal_dir]
    )
    find_custom_exact = _make_find_exact(
        custom_index, [logo_custom_single_dir, logo_custom_double_dir]
    )
    find_custom_logo = _make_find_prefix(
        custom_index,
        find_image_custom_logo_impl,
        [logo_custom_single_dir, logo_custom_double_dir],
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
            return None
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
