"""URL download, signature checks, and Pillow resize/compress for PDF images."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def looks_like_image_bytes_impl(data: bytes) -> bool:
    """Best-effort file-signature check for common image formats."""
    if not data or len(data) < 12:
        return False
    # JPEG
    if data.startswith(b"\xFF\xD8\xFF"):
        return True
    # PNG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # GIF
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return True
    # WEBP (RIFF....WEBP)
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return True
    # BMP
    if data.startswith(b"BM"):
        return True
    return False


def download_url_image_impl(
    url: str,
    *,
    timeout_sec: int,
    max_bytes: int,
) -> Optional[bytes]:
    """Download image bytes from URL with strict timeout/size/content checks."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "PackingListApp/1.0",
                "Accept": "image/*,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=timeout_sec) as resp:
            content_type = str(resp.headers.get("Content-Type", "")).lower()
            chunks: List[bytes] = []
            total = 0
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    return None
                chunks.append(chunk)
            data = b"".join(chunks)
            if not data:
                return None
            # Prefer MIME signal when available, but allow valid image bytes even if
            # the server reports a generic or incorrect content type.
            if content_type and "image" not in content_type and not looks_like_image_bytes_impl(data):
                return None
            if not looks_like_image_bytes_impl(data):
                return None
            return data
    except Exception:
        return None


def prepare_image_impl(
    path: Path,
    max_width_pt: float,
    max_height_pt: float,
    *,
    image_dpi: int,
    image_cache: Dict[Tuple[str, int, int], bytes],
    image_module: Any,
) -> Union[Path, io.BytesIO]:
    """Resize/compress image to fit within (max_width_pt, max_height_pt) at image_dpi.

    Uses caller-provided in-memory cache. Returns BytesIO when successful, else Path.
    """
    if image_module is None:
        return path

    # Convert from points to pixels for resizing and build a cache key.
    max_w_px = max(int(max_width_pt * image_dpi / 72.0), 1)
    max_h_px = max(int(max_height_pt * image_dpi / 72.0), 1)
    cache_key = (str(path), max_w_px, max_h_px)

    cached = image_cache.get(cache_key)
    if cached is not None:
        return io.BytesIO(cached)

    try:
        img = image_module.open(path)
    except Exception:
        return path

    # Determine if image has alpha channel
    has_alpha = img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in getattr(img, "info", {})
    )
    if img.mode not in ("RGB", "RGBA", "LA"):
        img = img.convert("RGBA" if has_alpha else "RGB")

    try:
        # Preserve aspect ratio while fitting within max box
        img.thumbnail((max_w_px, max_h_px), getattr(image_module, "LANCZOS", image_module.BICUBIC))
        buf = io.BytesIO()
        if has_alpha:
            img.save(buf, format="PNG", optimize=True)
        else:
            img.save(buf, format="JPEG", quality=85, optimize=True)
        data = buf.getvalue()
        image_cache[cache_key] = data
        return io.BytesIO(data)
    except Exception:
        return path


def prepare_image_bytes_impl(
    data: bytes,
    max_width_pt: float,
    max_height_pt: float,
    *,
    image_dpi: int,
    image_module: Any,
) -> Optional[io.BytesIO]:
    """Resize/compress raw image bytes to fit target box and return stream."""
    if not data:
        return None
    max_w_px = max(int(max_width_pt * image_dpi / 72.0), 1)
    max_h_px = max(int(max_height_pt * image_dpi / 72.0), 1)
    if image_module is None:
        return io.BytesIO(data)
    try:
        img = image_module.open(io.BytesIO(data))
    except Exception:
        return None
    has_alpha = img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in getattr(img, "info", {})
    )
    if img.mode not in ("RGB", "RGBA", "LA"):
        img = img.convert("RGBA" if has_alpha else "RGB")
    try:
        img.thumbnail((max_w_px, max_h_px), getattr(image_module, "LANCZOS", image_module.BICUBIC))
        out = io.BytesIO()
        if has_alpha:
            img.save(out, format="PNG", optimize=True)
        else:
            img.save(out, format="JPEG", quality=85, optimize=True)
        return io.BytesIO(out.getvalue())
    except Exception:
        return None


def prepare_image_from_url_impl(
    url: str,
    max_width_pt: float,
    max_height_pt: float,
    *,
    image_dpi: int,
    url_image_cache: Dict[Tuple[str, int, int], Optional[bytes]],
    image_module: Any,
    timeout_sec: int,
    max_bytes: int,
) -> Optional[io.BytesIO]:
    """Download, validate, and prepare URL image for drawing."""
    max_w_px = max(int(max_width_pt * image_dpi / 72.0), 1)
    max_h_px = max(int(max_height_pt * image_dpi / 72.0), 1)
    key = (url.strip(), max_w_px, max_h_px)
    if key in url_image_cache:
        cached = url_image_cache[key]
        return io.BytesIO(cached) if cached else None
    data = download_url_image_impl(url, timeout_sec=timeout_sec, max_bytes=max_bytes)
    if not data:
        url_image_cache[key] = None
        return None
    prepared = prepare_image_bytes_impl(
        data, max_width_pt, max_height_pt, image_dpi=image_dpi, image_module=image_module
    )
    if prepared is None:
        url_image_cache[key] = None
        return None
    prepared_data = prepared.getvalue()
    url_image_cache[key] = prepared_data
    return io.BytesIO(prepared_data)
