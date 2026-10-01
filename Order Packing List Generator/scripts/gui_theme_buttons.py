"""Button / scrollbar / labelframe ttk styles."""

from __future__ import annotations

from tkinter import ttk

from scripts.gui_theme_palette import (
    _ACCENT,
    _ACCENT_ACTIVE,
    _ACCENT_FG,
    _ACCENT_HOVER,
    _BG,
    _BORDER,
    _DISABLED_BG,
    _DISABLED_FG,
    _FONT_UI,
    _FONT_UI_BOLD,
    _LOG_BG,
    _MUTED,
    _SELECT_BG,
    _SURFACE,
    _TEXT,
)


def configure_button_styles(style: ttk.Style) -> None:
    style.configure(
        "TButton",
        background=_SURFACE,
        foreground=_TEXT,
        bordercolor=_BORDER,
        lightcolor=_BORDER,
        darkcolor=_BORDER,
        focuscolor=_SELECT_BG,
        font=_FONT_UI,
        padding=(12, 6),
    )
    style.map(
        "TButton",
        background=[("active", _LOG_BG), ("pressed", _BORDER), ("disabled", _DISABLED_BG)],
        foreground=[("disabled", _DISABLED_FG)],
        bordercolor=[("active", _ACCENT), ("disabled", _BORDER)],
    )

    style.configure(
        "Accent.TButton",
        background=_ACCENT,
        foreground=_ACCENT_FG,
        bordercolor=_ACCENT,
        lightcolor=_ACCENT,
        darkcolor=_ACCENT_ACTIVE,
        focuscolor=_ACCENT_HOVER,
        font=_FONT_UI_BOLD,
        padding=(14, 7),
    )
    style.map(
        "Accent.TButton",
        background=[
            ("active", _ACCENT_HOVER),
            ("pressed", _ACCENT_ACTIVE),
            ("disabled", _BORDER),
        ],
        foreground=[("disabled", _MUTED)],
        bordercolor=[
            ("active", _ACCENT_HOVER),
            ("pressed", _ACCENT_ACTIVE),
            ("disabled", _BORDER),
        ],
    )

    style.configure(
        "Chip.TButton",
        background=_SURFACE,
        foreground=_TEXT,
        bordercolor=_BORDER,
        lightcolor=_BORDER,
        darkcolor=_BORDER,
        focuscolor=_SELECT_BG,
        font=_FONT_UI,
        padding=(8, 3),
    )
    style.map(
        "Chip.TButton",
        background=[("active", _SELECT_BG), ("pressed", _BORDER), ("disabled", _DISABLED_BG)],
        foreground=[("disabled", _DISABLED_FG)],
        bordercolor=[("active", _ACCENT), ("disabled", _BORDER)],
    )

    style.configure(
        "TScrollbar",
        background=_BORDER,
        troughcolor=_LOG_BG,
        bordercolor=_BG,
        arrowcolor=_TEXT,
    )
    style.map("TScrollbar", background=[("active", _MUTED)])

    style.configure(
        "TLabelframe",
        background=_BG,
        foreground=_TEXT,
        bordercolor=_BORDER,
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=_BG,
        foreground=_MUTED,
        font=_FONT_UI_BOLD,
    )
