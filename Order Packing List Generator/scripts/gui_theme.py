"""Shared dark-industrial Tk theme for packing GUIs — stable façade."""

from __future__ import annotations

from scripts.gui_theme_apply import apply_theme
from scripts.gui_theme_chips import (
    _reflow_tag_chips,
    refresh_tag_chip_grid,
    set_tag_chip_grid_enabled,
)
from scripts.gui_theme_forms import make_log_text, make_scrollable_form, show_scrollable_message
from scripts.gui_theme_palette import (
    _ACCENT,
    _ACCENT_ACTIVE,
    _ACCENT_FG,
    _ACCENT_HOVER,
    _BG,
    _BORDER,
    _DISABLED_BG,
    _DISABLED_FG,
    _FONT_LOG,
    _FONT_TITLE,
    _FONT_UI,
    _FONT_UI_BOLD,
    _LOG_BG,
    _LOG_FG,
    _MUTED,
    _SELECT_BG,
    _SELECT_FG,
    _SURFACE,
    _TEXT,
)
from scripts.gui_theme_widgets import set_listbox_enabled, style_listbox, style_log_text

__all__ = [
    "apply_theme",
    "style_log_text",
    "style_listbox",
    "set_listbox_enabled",
    "refresh_tag_chip_grid",
    "set_tag_chip_grid_enabled",
    "make_scrollable_form",
    "make_log_text",
    "show_scrollable_message",
]
