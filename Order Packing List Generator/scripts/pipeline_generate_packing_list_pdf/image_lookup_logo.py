"""Normal / custom logo prefix lookup helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from pipeline_generate_packing_list_pdf.image_lookup_side_skip import (
    skip_custom_logo_prefix_stem,
)
from pipeline_generate_packing_list_pdf.image_lookup_stem import (
    _demo_fallback,
    _path_if_file,
    _remember_stem,
    probe_exact_image_impl,
)


def find_image_normal_logo_impl(
    root_dir: Optional[Path],
    token: str,
    stem_map: Optional[Dict[str, Path]],
    *,
    recursive: bool = False,
) -> Optional[Path]:
    """Normal Logo lookup: exact stem, then prefix (skipping LOCATION / F/B/P/S sides)."""
    if not token:
        return None
    if stem_map is not None:
        exact = _path_if_file(stem_map.get(token))
        if exact is not None:
            return exact
        for stem, path in stem_map.items():
            if stem.startswith(token) and not skip_custom_logo_prefix_stem(stem, token):
                found = _path_if_file(path)
                if found is not None:
                    return found
        token_lower = token.lower()
        for stem, path in stem_map.items():
            if stem.lower().startswith(token_lower) and not skip_custom_logo_prefix_stem(
                stem, token
            ):
                found = _path_if_file(path)
                if found is not None:
                    return found
        live = probe_exact_image_impl(root_dir, token)
        if live is not None and not skip_custom_logo_prefix_stem(live.stem, token):
            return _remember_stem(stem_map, live.stem, live)
        fb = _demo_fallback("normal", token)
        if fb is not None:
            return fb
        return None
    if not root_dir or not root_dir.is_dir():
        fb = _demo_fallback("normal", token)
        return fb
    live = probe_exact_image_impl(root_dir, token)
    if live is not None:
        return live
    for ext in (".png", ".jpg", ".jpeg"):
        iterator = root_dir.rglob(f"*{ext}") if recursive else root_dir.glob(f"*{ext}")
        for p in iterator:
            if (
                p.is_file()
                and p.stem.startswith(token)
                and not skip_custom_logo_prefix_stem(p.stem, token)
            ):
                return p
    token_lower = token.lower()
    for ext in (".png", ".jpg", ".jpeg"):
        iterator = root_dir.rglob(f"*{ext}") if recursive else root_dir.glob(f"*{ext}")
        for p in iterator:
            if (
                p.is_file()
                and p.stem.lower().startswith(token_lower)
                and not skip_custom_logo_prefix_stem(p.stem, token)
            ):
                return p
    return _demo_fallback("normal", token)
