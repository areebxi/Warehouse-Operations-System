"""Demo image folders for offline / dev testing without UK design or apparel storage."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from shared import paths as wh

_DEMO_FILENAME = "demo.png"

_active = False
_paths: dict[str, Path] = {}


def demo_fallback_path(kind: str, token: str) -> Optional[Path]:
    """Return demo placeholder when lookup is active and token expects an image."""
    if not _active:
        return None
    if not (token or "").strip():
        return None
    path = _paths.get(kind)
    if path is not None and path.is_file():
        return path
    return None


@contextmanager
def demo_image_lookup(enabled: bool = True) -> Iterator[None]:
    """Activate demo fallbacks in shared image lookup for the current thread."""
    global _active, _paths
    if not enabled:
        yield
        return
    ensure_demo_images()
    _paths = {
        "apparel": wh.demo_apparel_dir() / _DEMO_FILENAME,
        "normal": wh.demo_normal_design_dir() / _DEMO_FILENAME,
        "custom": wh.demo_custom_single_dir() / _DEMO_FILENAME,
        "custom_double": wh.demo_custom_double_dir() / _DEMO_FILENAME,
    }
    _active = True
    try:
        yield
    finally:
        _active = False
        _paths = {}


def effective_image_dirs(
    use_demo: bool,
    apparel: object | None,
    logo_normal: object | None,
    logo_custom_single: object | None,
    logo_custom_double: object | None,
    *,
    from_path: object | None = None,
) -> tuple[Optional[Path], Optional[Path], Optional[Path], Optional[Path]]:
    """Resolve GUI paths; demo folders override when ``use_demo`` is True."""
    if use_demo:
        ensure_demo_images(from_path=from_path)
        return (
            wh.demo_apparel_dir(from_path),
            wh.demo_normal_design_dir(from_path),
            wh.demo_custom_single_dir(from_path),
            wh.demo_custom_double_dir(from_path),
        )

    def _opt(value: object | None) -> Optional[Path]:
        if value is None:
            return None
        text = str(value).strip()
        return Path(text) if text else None

    return (
        _opt(apparel),
        _opt(logo_normal),
        _opt(logo_custom_single),
        _opt(logo_custom_double),
    )


def ensure_demo_images(*, from_path: object | None = None) -> None:
    """Create demo folders and placeholder PNGs if missing."""
    specs = (
        (wh.demo_apparel_dir(from_path), "DEMO APPAREL", (180, 180, 200)),
        (wh.demo_normal_design_dir(from_path), "DEMO LOGO", (120, 200, 120)),
        (wh.demo_custom_single_dir(from_path), "DEMO SINGLE", (200, 160, 120)),
        (wh.demo_custom_double_dir(from_path), "DEMO DOUBLE", (200, 120, 160)),
    )
    for folder, label, rgb in specs:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / _DEMO_FILENAME
        if target.is_file():
            continue
        _write_placeholder_png(target, label, rgb)


def _write_placeholder_png(path: Path, label: str, rgb: tuple[int, int, int]) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        # ponytail: minimal 1×1 PNG if Pillow missing (lookup still succeeds)
        path.write_bytes(
            bytes.fromhex(
                "89504e470d0a1a0a0000000d49484452"
                "000000010000000108060000001f15c489"
                "0000000a49444154789c6300010000050001"
                "0d0a2db40000000049454e44ae426082"
            )
        )
        return

    size = 512
    img = Image.new("RGB", (size, size), rgb)
    draw = ImageDraw.Draw(img)
    draw.rectangle([16, 16, size - 17, size - 17], outline=(40, 40, 40), width=4)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.multiline_text((size // 2, size // 2), label, fill=(20, 20, 20), anchor="mm", align="center", font=font)
    img.save(path, format="PNG")
