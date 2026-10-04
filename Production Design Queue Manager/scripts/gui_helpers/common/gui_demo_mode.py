"""Testing-mode helpers for Queue App (demo design folders + lookup fallbacks)."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


def _warehouse_root() -> Path:
    return Path(__file__).resolve().parents[4]


def use_demo(gui) -> bool:
    var = getattr(gui, "use_demo_images_var", None)
    if var is not None:
        return bool(var.get())
    return bool(getattr(gui, "use_demo_images", False))


def resolve_design_folders(
    gui,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    root = _warehouse_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from shared.demo_images import effective_design_dirs

    designs, single, double = effective_design_dirs(
        use_demo(gui),
        getattr(gui, "designs_folder", None),
        getattr(gui, "single_designs_folder", None),
        getattr(gui, "double_designs_folder", None),
        from_path=root,
    )
    return (
        str(designs) if designs else None,
        str(single) if single else None,
        str(double) if double else None,
    )


def apply_resolved_folders(gui) -> None:
    """Set gui folder attrs from offline mode or saved GUI paths."""
    designs, single, double = resolve_design_folders(gui)
    gui.designs_folder = designs
    gui.single_designs_folder = single
    gui.double_designs_folder = double


def has_missing_logo_folders(gui) -> bool:
    if use_demo(gui):
        return True
    return bool(
        gui.single_designs_folder or gui.double_designs_folder or gui.designs_folder
    )


@contextmanager
def queue_demo_lookup(gui) -> Iterator[None]:
    root = _warehouse_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from shared.demo_images import demo_image_lookup

    apply_resolved_folders(gui)
    with demo_image_lookup(use_demo(gui)):
        yield
