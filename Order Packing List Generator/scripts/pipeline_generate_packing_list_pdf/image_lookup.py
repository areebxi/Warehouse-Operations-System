"""Filesystem image path lookup (stem maps, apparel/logo resolution)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.stem_map_cache import (
    load_stem_map_from_disk,
    save_stem_map_to_disk,
)

_IMAGE_EXTS = {".png", ".jpg", ".jpeg"}

# (resolved_abs_path, recursive) -> stem map for the current process.
_MEMORY_STEM_MAPS: Dict[Tuple[str, bool], Dict[str, Path]] = {}


def clear_stem_map_caches() -> None:
    """Clear in-process stem maps (tests / forced refresh). Disk cache is left intact."""
    _MEMORY_STEM_MAPS.clear()


def _count_image_files(root: Path, *, recursive: bool) -> int:
    """Cheap image-file count used to invalidate stale Google Drive caches."""
    root_str = str(root)
    count = 0
    if recursive:
        for _dirpath, _dirnames, filenames in os.walk(root_str):
            for name in filenames:
                if os.path.splitext(name)[1].lower() in _IMAGE_EXTS:
                    count += 1
        return count
    try:
        with os.scandir(root_str) as it:
            for entry in it:
                if not entry.is_file(follow_symlinks=False):
                    continue
                if os.path.splitext(entry.name)[1].lower() in _IMAGE_EXTS:
                    count += 1
    except OSError:
        return -1
    return count


def probe_exact_image_impl(root_dir: Optional[Path], base_name: str) -> Optional[Path]:
    """O(1) check for ``{base_name}.png|.jpg|.jpeg`` directly under root_dir (no directory scan)."""
    if not base_name or root_dir is None:
        return None
    try:
        if not root_dir.is_dir():
            return None
    except OSError:
        return None
    for ext in (".png", ".jpg", ".jpeg"):
        p = root_dir / f"{base_name}{ext}"
        try:
            if p.is_file():
                return p
        except OSError:
            continue
    return None


def find_image_in_dir_impl(
    root_dir: Path, base_name: str, *, recursive: bool = False
) -> Optional[Path]:
    """Find a file with stem == base_name and extension .png, .jpg, or .jpeg in root_dir.
    If recursive is True, search root_dir and all subfolders; if False, only top-level files in root_dir.
    Return first match or None."""
    if not base_name or not root_dir or not root_dir.is_dir():
        return None
    # Non-recursive: probe exact filenames only (full glob of 100k+ Drive files hangs).
    if not recursive:
        return probe_exact_image_impl(root_dir, base_name)
    for ext in (".png", ".jpg", ".jpeg"):
        for p in root_dir.rglob(f"*{ext}"):
            if p.is_file() and p.stem == base_name:
                return p
    return None


def _scan_image_stem_map(root: Path, *, recursive: bool) -> Dict[str, Path]:
    """One-pass directory scan -> stem map (no caching)."""
    result: Dict[str, Path] = {}
    root_str = str(root)

    def _maybe_add(dirpath: str, name: str) -> None:
        stem, ext = os.path.splitext(name)
        if ext.lower() not in _IMAGE_EXTS:
            return
        if stem in result:
            return
        result[stem] = Path(dirpath) / name

    if recursive:
        for dirpath, _dirnames, filenames in os.walk(root_str):
            for name in filenames:
                _maybe_add(dirpath, name)
    else:
        with os.scandir(root_str) as it:
            for entry in it:
                if not entry.is_file(follow_symlinks=False):
                    continue
                _maybe_add(root_str, entry.name)
    return result


def build_image_stem_map_impl(
    root_dir: Optional[Path], *, recursive: bool = False
) -> Optional[Dict[str, Path]]:
    """Build a dict stem -> Path for image files in root_dir.

    When recursive is True, search subfolders; when False, top-level only.
    Uses in-process memory cache, then on-disk cache (mtime + entry count), then
    a single os.scandir / os.walk pass. Returns None if root_dir is None or not a directory.
    """
    if root_dir is None:
        return None
    try:
        if not root_dir.is_dir():
            return None
        resolved = str(root_dir.resolve())
        mtime_ns = root_dir.stat().st_mtime_ns
    except OSError:
        return None

    cache_key = (resolved, bool(recursive))
    cached = _MEMORY_STEM_MAPS.get(cache_key)
    if cached is not None:
        return cached

    entry_count = _count_image_files(Path(resolved), recursive=bool(recursive))
    disk = (
        load_stem_map_from_disk(resolved, bool(recursive), mtime_ns, entry_count)
        if entry_count >= 0
        else None
    )
    if disk is not None:
        _MEMORY_STEM_MAPS[cache_key] = disk
        return disk

    result = _scan_image_stem_map(Path(resolved), recursive=bool(recursive))
    _MEMORY_STEM_MAPS[cache_key] = result
    save_stem_map_to_disk(
        resolved, bool(recursive), mtime_ns, result, entry_count=entry_count
    )
    return result


def _path_if_file(path: Optional[Path]) -> Optional[Path]:
    """Return path only when it still exists (guards against stale stem-map entries)."""
    if path is None:
        return None
    try:
        p = Path(path)
        return p if p.is_file() else None
    except OSError:
        return None


def _remember_stem(stem_map: Optional[Dict[str, Path]], stem: str, path: Path) -> Path:
    """Update in-memory stem map when a live lookup finds a file the cache missed."""
    if stem_map is not None and stem:
        stem_map[stem] = path
    return path


def find_image_impl(
    root_dir: Optional[Path],
    base_name: str,
    stem_map: Optional[Dict[str, Path]],
    *,
    recursive: bool = False,
) -> Optional[Path]:
    """Return Path for base_name in root_dir, using stem_map if provided else directory search (recursive or top-level only)."""
    if not base_name:
        return None
    if stem_map is not None:
        found = _path_if_file(stem_map.get(base_name))
        if found is not None:
            return found
        # Case-insensitive fallback (e.g. "Only-Design-Iron-On-Sticker" vs "only-design-iron-on-sticker")
        lower = base_name.lower()
        for stem, path in stem_map.items():
            if stem.lower() == lower:
                found = _path_if_file(path)
                if found is not None:
                    return found
        # Map miss: cheap exact probe only (never full-scan huge Drive folders).
        live = probe_exact_image_impl(root_dir, base_name)
        if live is not None:
            return _remember_stem(stem_map, live.stem, live)
        return None
    if not root_dir or not root_dir.is_dir():
        return None
    return find_image_in_dir_impl(root_dir, base_name, recursive=recursive)


def find_image_normal_logo_impl(
    root_dir: Optional[Path],
    token: str,
    stem_map: Optional[Dict[str, Path]],
    *,
    recursive: bool = False,
) -> Optional[Path]:
    """Like find_image_impl but for Normal Logo/Design folder: try exact stem match first, then first file whose stem starts with token (e.g. 8513LG or 8513LG i found this humerus)."""
    if not token:
        return None
    if stem_map is not None:
        exact = _path_if_file(stem_map.get(token))
        if exact is not None:
            return exact
        for stem, path in stem_map.items():
            if stem.startswith(token):
                found = _path_if_file(path)
                if found is not None:
                    return found
        # Case-insensitive fallback: token/filename case mismatch
        token_lower = token.lower()
        for stem, path in stem_map.items():
            if stem.lower().startswith(token_lower):
                found = _path_if_file(path)
                if found is not None:
                    return found
        live = probe_exact_image_impl(root_dir, token)
        if live is not None:
            return _remember_stem(stem_map, live.stem, live)
        return None
    if not root_dir or not root_dir.is_dir():
        return None
    # No stem map: exact probe first, then (expensive) prefix scan only if recursive or small dirs.
    live = probe_exact_image_impl(root_dir, token)
    if live is not None:
        return live
    for ext in (".png", ".jpg", ".jpeg"):
        iterator = root_dir.rglob(f"*{ext}") if recursive else root_dir.glob(f"*{ext}")
        for p in iterator:
            if p.is_file() and p.stem.startswith(token):
                return p
    token_lower = token.lower()
    for ext in (".png", ".jpg", ".jpeg"):
        iterator = root_dir.rglob(f"*{ext}") if recursive else root_dir.glob(f"*{ext}")
        for p in iterator:
            if p.is_file() and p.stem.lower().startswith(token_lower):
                return p
    return None


def find_image_custom_fbpi_impl(
    stem_map: Optional[Dict[str, Path]],
    base_token: str,
) -> Optional[Path]:
    """Find Customise F/B/P/I image by exact stem, then by stems starting with base_token.

    Used only with the pre-built logo_custom_stem_map for the Customise Logo/Design
    folder. Lookup order:
      1. Exact stem == base_token
      2. First stem that startswith(base_token) (case-sensitive)
      3. First stem that startswith(base_token.lower()) (case-insensitive)
    Returns the corresponding Path or None.
    """
    if not base_token or stem_map is None:
        return None

    exact = _path_if_file(stem_map.get(base_token))
    if exact is not None:
        return exact

    for stem, path in stem_map.items():
        if stem.startswith(base_token):
            found = _path_if_file(path)
            if found is not None:
                return found

    base_lower = base_token.lower()
    for stem, path in stem_map.items():
        if stem.lower().startswith(base_lower):
            found = _path_if_file(path)
            if found is not None:
                return found

    return None


def find_image_custom_exact_impl(
    root_dir: Optional[Path],
    token: str,
    stem_map: Optional[Dict[str, Path]],
    *,
    recursive: bool = True,
) -> Optional[Path]:
    """Find custom image by exact stem only (no prefix fallback)."""
    if not token:
        return None
    if stem_map is not None:
        exact = _path_if_file(stem_map.get(token))
        if exact is not None:
            return exact
        token_lower = token.lower()
        for stem, path in stem_map.items():
            if stem.lower() == token_lower:
                found = _path_if_file(path)
                if found is not None:
                    return found
        live = probe_exact_image_impl(root_dir, token)
        if live is not None:
            return _remember_stem(stem_map, live.stem, live)
        return None
    if not root_dir or not root_dir.is_dir():
        return None
    live = probe_exact_image_impl(root_dir, token)
    if live is not None:
        return live
    if not recursive:
        return None
    token_lower = token.lower()
    for ext in (".png", ".jpg", ".jpeg"):
        for p in root_dir.rglob(f"*{ext}"):
            if p.is_file() and p.stem.lower() == token_lower:
                return p
    return None


def find_image_custom_logo_impl(
    root_dir: Optional[Path],
    token: str,
    stem_map: Optional[Dict[str, Path]],
    *,
    recursive: bool = True,
) -> Optional[Path]:
    """Find a logo/design image by token in the custom directory or stem map.

    Same lookup order as find_image_normal_logo_impl: exact stem match, then stem
    starting with token, then case-insensitive. Used when Customise=Yes and we
    look up each Logo/Design Image token in the custom dirs.
    """
    if not token:
        return None
    if stem_map is not None:
        exact = _path_if_file(stem_map.get(token))
        if exact is not None:
            return exact
        for stem, path in stem_map.items():
            if stem.startswith(token):
                found = _path_if_file(path)
                if found is not None:
                    return found
        token_lower = token.lower()
        for stem, path in stem_map.items():
            if stem.lower().startswith(token_lower):
                found = _path_if_file(path)
                if found is not None:
                    return found
        live = probe_exact_image_impl(root_dir, token)
        if live is not None:
            return _remember_stem(stem_map, live.stem, live)
        return None
    if not root_dir or not root_dir.is_dir():
        return None
    live = probe_exact_image_impl(root_dir, token)
    if live is not None:
        return live
    for ext in (".png", ".jpg", ".jpeg"):
        iterator = root_dir.rglob(f"*{ext}") if recursive else root_dir.glob(f"*{ext}")
        for p in iterator:
            if p.is_file() and p.stem.startswith(token):
                return p
    token_lower = token.lower()
    for ext in (".png", ".jpg", ".jpeg"):
        iterator = root_dir.rglob(f"*{ext}") if recursive else root_dir.glob(f"*{ext}")
        for p in iterator:
            if p.is_file() and p.stem.lower().startswith(token_lower):
                return p
    return None
