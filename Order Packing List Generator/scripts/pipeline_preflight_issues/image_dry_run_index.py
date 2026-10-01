"""Stem indexes and find-call factories for preflight image dry-run."""

from __future__ import annotations

import bisect
from pathlib import Path
from typing import Dict, List, Optional

from pipeline_generate_packing_list_pdf.images import find_image_impl
from pipeline_generate_packing_list_pdf.image_lookup import probe_exact_image_impl
from shared.demo_images import demo_fallback_path

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
    *,
    demo_kind: str = "apparel",
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
            return demo_fallback_path(demo_kind, base_name)
        return find_image_impl(root_dir, base_name, stem_map, recursive=recursive)

    return _find


def _make_find_prefix(
    index: Optional[_StemIndex],
    fallback_fn,
    fallback_dirs: Optional[List[Optional[Path]]] = None,
    *,
    demo_kind: str = "normal",
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
            return demo_fallback_path(demo_kind, token)
        return fallback_fn(root_dir, token, stem_map, recursive=recursive)

    return _find
