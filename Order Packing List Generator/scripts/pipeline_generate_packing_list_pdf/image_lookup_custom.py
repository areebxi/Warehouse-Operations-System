"""Custom logo prefix/exact lookup helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from pipeline_generate_packing_list_pdf.image_lookup_stem import (
    _demo_fallback,
    _path_if_file,
    _remember_stem,
    probe_exact_image_impl,
)

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

    return _demo_fallback("custom", base_token)


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
        fb = _demo_fallback("custom", token)
        if fb is not None:
            return fb
        return None
    if not root_dir or not root_dir.is_dir():
        fb = _demo_fallback("custom", token)
        return fb
    live = probe_exact_image_impl(root_dir, token)
    if live is not None:
        return live
    if not recursive:
        return _demo_fallback("custom", token)
    token_lower = token.lower()
    for ext in (".png", ".jpg", ".jpeg"):
        for p in root_dir.rglob(f"*{ext}"):
            if p.is_file() and p.stem.lower() == token_lower:
                return p
    return _demo_fallback("custom", token)


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
        fb = _demo_fallback("custom", token)
        if fb is not None:
            return fb
        return None
    if not root_dir or not root_dir.is_dir():
        fb = _demo_fallback("custom", token)
        return fb
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
    return _demo_fallback("custom", token)
