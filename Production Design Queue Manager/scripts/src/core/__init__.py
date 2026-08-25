"""
Core application logic (canvas/image algorithms).

This package re-exports the legacy flat modules from `src/` so existing code
and tests remain stable while imports can move to a modular structure.
"""

from .canvas_arranger import pack_designs
from .image_utils import DEFAULT_DESIGN_PADDING

__all__ = [
    "pack_designs",
    "DEFAULT_DESIGN_PADDING",
]

