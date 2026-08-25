"""On-disk stem-map cache for image folder indexes."""

from __future__ import annotations

import hashlib
import os
import pickle
import sys
from pathlib import Path
from typing import Dict, Optional

# v2: shared cache dir + entry_count fingerprint (mtime alone is unreliable on Google Drive).
_CACHE_VERSION = 2


def stem_map_cache_dir() -> Path:
    """Writable directory for pickled stem maps (shared across app copies)."""
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    shared = local / "PackingListApp" / "cache" / "image_stem_maps"
    candidates: list[Path] = [shared]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys.executable).resolve().parent / "cache" / "image_stem_maps")
    for c in candidates:
        try:
            c.mkdir(parents=True, exist_ok=True)
            probe = c / ".write_probe"
            probe.write_text("", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return c.resolve()
        except OSError:
            continue
    shared.mkdir(parents=True, exist_ok=True)
    return shared.resolve()


def _cache_file_path(resolved_root: str, recursive: bool) -> Path:
    key = f"{resolved_root}|{int(recursive)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]
    return stem_map_cache_dir() / f"{digest}.pkl"


def load_stem_map_from_disk(
    resolved_root: str,
    recursive: bool,
    mtime_ns: int,
    entry_count: int,
) -> Optional[Dict[str, Path]]:
    """Return stem map if a valid disk cache exists for this folder fingerprint."""
    path = _cache_file_path(resolved_root, recursive)
    if not path.is_file():
        return None
    try:
        with path.open("rb") as fh:
            payload = pickle.load(fh)
    except (OSError, pickle.PickleError, EOFError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("version") != _CACHE_VERSION:
        return None
    if payload.get("root") != resolved_root or bool(payload.get("recursive")) != recursive:
        return None
    if payload.get("mtime_ns") != mtime_ns:
        return None
    if int(payload.get("entry_count", -1)) != int(entry_count):
        return None
    raw = payload.get("stem_to_path")
    if not isinstance(raw, dict):
        return None
    return {str(stem): Path(p) for stem, p in raw.items()}


def save_stem_map_to_disk(
    resolved_root: str,
    recursive: bool,
    mtime_ns: int,
    stem_map: Dict[str, Path],
    *,
    entry_count: int,
) -> None:
    """Persist stem map for later sessions when folder fingerprint is unchanged."""
    path = _cache_file_path(resolved_root, recursive)
    payload = {
        "version": _CACHE_VERSION,
        "root": resolved_root,
        "recursive": recursive,
        "mtime_ns": mtime_ns,
        # Image *file* count (not unique stems) — matches _count_image_files.
        "entry_count": int(entry_count),
        "stem_to_path": {stem: str(p) for stem, p in stem_map.items()},
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with tmp.open("wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)
    except OSError:
        try:
            tmp = path.with_suffix(".tmp")
            if tmp.is_file():
                tmp.unlink(missing_ok=True)
        except OSError:
            pass
