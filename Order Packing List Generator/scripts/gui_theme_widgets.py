"""Listbox / Text styling helpers for packing GUIs."""

from __future__ import annotations

from tkinter import DISABLED, Listbox, NORMAL, Text

from scripts.gui_theme_palette import (
    _ACCENT,
    _ACCENT_FG,
    _BORDER,
    _DISABLED_BG,
    _DISABLED_FG,
    _FONT_LOG,
    _FONT_UI,
    _LOG_BG,
    _LOG_FG,
    _SELECT_BG,
    _SELECT_FG,
    _SURFACE,
    _TEXT,
)


def style_log_text(widget: Text) -> Text:
    """Apply a quiet monospace look to a log Text widget."""
    widget.configure(
        background=_LOG_BG,
        foreground=_LOG_FG,
        insertbackground=_TEXT,
        selectbackground=_SELECT_BG,
        selectforeground=_SELECT_FG,
        font=_FONT_LOG,
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=_BORDER,
        highlightcolor=_ACCENT,
        padx=8,
        pady=8,
    )
    return widget


def style_listbox(widget: Listbox) -> Listbox:
    """Match Listbox colors to the shared theme."""
    widget.configure(
        background=_SURFACE,
        foreground=_TEXT,
        selectbackground=_ACCENT,
        selectforeground=_ACCENT_FG,
        font=_FONT_UI,
        relief="flat",
        borderwidth=1,
        highlightthickness=1,
        highlightbackground=_BORDER,
        highlightcolor=_ACCENT,
        activestyle="none",
        disabledforeground=_DISABLED_FG,
    )
    return widget


def set_listbox_enabled(widget: Listbox, enabled: bool) -> None:
    """Enable/disable a Listbox and grey it out when blocked."""
    if enabled:
        widget.configure(
            state=NORMAL,
            background=_SURFACE,
            foreground=_TEXT,
            highlightbackground=_BORDER,
        )
    else:
        widget.configure(
            state=DISABLED,
            background=_DISABLED_BG,
            foreground=_DISABLED_FG,
            highlightbackground=_BORDER,
        )
