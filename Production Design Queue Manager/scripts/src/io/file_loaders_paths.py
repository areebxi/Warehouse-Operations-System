"""Queue path helpers + Color Bar loader."""

from __future__ import annotations

import os
from typing import Optional, Tuple

from PIL import Image


def _resolve_project_root_from_module() -> str:
    """Resolve project root from scripts/src/io module location."""
    io_dir = os.path.dirname(os.path.abspath(__file__))  # .../scripts/src/io
    src_dir = os.path.dirname(io_dir)  # .../scripts/src
    scripts_dir = os.path.dirname(src_dir)  # .../scripts
    project_root = os.path.dirname(scripts_dir)  # project root
    return project_root


def _warehouse_queue_paths():
    import sys
    from pathlib import Path

    app_root = Path(_resolve_project_root_from_module())
    warehouse = app_root.parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    return wh


def load_color_bar_from_app_dir(app_dir: Optional[str] = None) -> Tuple[Optional[Image.Image], Optional[str]]:
    """Auto-load Color Bar file from Data/Queue (or legacy app dirs)."""
    try:
        wh = _warehouse_queue_paths()
        color_bar_names = ["Color Bar.png", "ColorBar.png", "color_bar.png", "colorbar.png"]
        if app_dir is None:
            app_dir = _resolve_project_root_from_module()
        search_dirs = [str(wh.queue_config_dir()), app_dir]

        for search_dir in search_dirs:
            for name in color_bar_names:
                file_path = os.path.join(search_dir, name)
                if not os.path.exists(file_path):
                    continue
                try:
                    color_bar_image = Image.open(file_path)
                    print(f"Color Bar loaded from: {file_path}")
                    return color_bar_image, file_path
                except Exception as e:
                    print(f"Error loading Color Bar from {file_path}: {e}")
                    continue
    except Exception as e:
        print(f"Error loading Color Bar from app directory: {e}")

    return None, None
