"""ttk style configuration for packing GUIs."""

from __future__ import annotations

from tkinter import Tk, ttk

from scripts.gui_theme_buttons import configure_button_styles
from scripts.gui_theme_palette import (
    _ACCENT,
    _BG,
    _BORDER,
    _DISABLED_BG,
    _DISABLED_FG,
    _FONT_TITLE,
    _FONT_UI,
    _MUTED,
    _SELECT_BG,
    _SELECT_FG,
    _SURFACE,
    _TEXT,
)


def apply_theme(root: Tk) -> ttk.Style:
    """Configure root window + ttk styles. Call once before building widgets."""
    root.configure(bg=_BG)
    try:
        root.option_add("*Font", _FONT_UI)
    except Exception:
        pass

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".", background=_BG, foreground=_TEXT, font=_FONT_UI)
    style.configure("TFrame", background=_BG)
    style.configure("Card.TFrame", background=_SURFACE)
    style.configure("TLabel", background=_BG, foreground=_TEXT, font=_FONT_UI)
    style.configure("Muted.TLabel", background=_BG, foreground=_MUTED, font=_FONT_UI)
    style.configure("Title.TLabel", background=_BG, foreground=_TEXT, font=_FONT_TITLE)

    style.configure(
        "TEntry",
        fieldbackground=_SURFACE,
        foreground=_TEXT,
        bordercolor=_BORDER,
        lightcolor=_ACCENT,
        darkcolor=_BORDER,
        insertcolor=_TEXT,
        padding=5,
    )
    style.map(
        "TEntry",
        fieldbackground=[("disabled", _DISABLED_BG)],
        foreground=[("disabled", _DISABLED_FG)],
        bordercolor=[("focus", _ACCENT), ("disabled", _BORDER)],
        lightcolor=[("focus", _ACCENT), ("disabled", _BORDER)],
    )

    style.configure(
        "TCombobox",
        fieldbackground=_SURFACE,
        foreground=_TEXT,
        bordercolor=_BORDER,
        lightcolor=_ACCENT,
        darkcolor=_BORDER,
        arrowcolor=_TEXT,
        padding=4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("disabled", _DISABLED_BG), ("readonly", _SURFACE)],
        background=[("disabled", _DISABLED_BG), ("readonly", _SURFACE)],
        foreground=[("disabled", _DISABLED_FG)],
        arrowcolor=[("disabled", _DISABLED_FG)],
        selectbackground=[("disabled", _DISABLED_BG), ("readonly", _SELECT_BG)],
        selectforeground=[("disabled", _DISABLED_FG), ("readonly", _SELECT_FG)],
        bordercolor=[("focus", _ACCENT), ("disabled", _BORDER)],
    )

    style.configure(
        "TCheckbutton",
        background=_BG,
        foreground=_TEXT,
        font=_FONT_UI,
        focuscolor=_BG,
    )
    style.map(
        "TCheckbutton",
        background=[("active", _BG)],
        foreground=[("disabled", _DISABLED_FG)],
        indicatorcolor=[
            ("disabled", _DISABLED_BG),
            ("selected", _ACCENT),
            ("!selected", _SURFACE),
        ],
    )

    style.configure(
        "TRadiobutton",
        background=_BG,
        foreground=_TEXT,
        font=_FONT_UI,
        focuscolor=_BG,
    )
    style.map(
        "TRadiobutton",
        background=[("active", _BG)],
        foreground=[("disabled", _DISABLED_FG)],
        indicatorcolor=[
            ("disabled", _DISABLED_BG),
            ("selected", _ACCENT),
            ("!selected", _SURFACE),
        ],
    )

    configure_button_styles(style)
    return style
