"""
Lightweight ttk theme for Queue App.

Applied once at UI creation. No per-frame work, no extra dependencies.
"""

from tkinter import ttk

# Cool slate palette — readable, calm, works on Windows clam theme
BG = "#eef1f5"
SURFACE = "#f7f9fc"
FG = "#1e293b"
MUTED = "#64748b"
BORDER = "#c5cede"
ACCENT = "#0f766e"
ACCENT_ACTIVE = "#0d9488"
ACCENT_PRESSED = "#115e59"
SECONDARY = "#334155"
SECONDARY_ACTIVE = "#475569"
PROGRESS_TROUGH = "#d7dee8"
PREVIEW_BG = "#d0d5dd"
PREVIEW_BG_RGBA = (208, 213, 221, 255)

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_HINT = ("Segoe UI", 8)


def apply_theme(root) -> ttk.Style:
    """Configure root + ttk styles once. Safe to call again (idempotent)."""
    style = ttk.Style(root)

    # clam allows reliable color customization across platforms
    try:
        style.theme_use("clam")
    except Exception:
        pass

    root.configure(bg=BG)

    style.configure(".", background=BG, foreground=FG, font=FONT_UI)
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG, font=FONT_UI)
    style.configure(
        "Muted.TLabel",
        background=BG,
        foreground=MUTED,
        font=FONT_UI,
    )
    style.configure(
        "Hint.TLabel",
        background=BG,
        foreground=MUTED,
        font=FONT_HINT,
    )

    style.configure(
        "TLabelframe",
        background=BG,
        foreground=FG,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=BG,
        foreground=FG,
        font=FONT_UI_BOLD,
    )

    style.configure(
        "TButton",
        background=SURFACE,
        foreground=FG,
        bordercolor=BORDER,
        lightcolor=SURFACE,
        darkcolor=BORDER,
        focuscolor=ACCENT,
        padding=(12, 7),
        font=FONT_UI,
    )
    style.map(
        "TButton",
        background=[("active", "#e2e8f0"), ("pressed", "#cbd5e1")],
        foreground=[("disabled", MUTED)],
        bordercolor=[("active", ACCENT)],
    )

    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT,
        lightcolor=ACCENT,
        darkcolor=ACCENT_PRESSED,
        focuscolor=ACCENT_ACTIVE,
        padding=(12, 8),
        font=FONT_UI_BOLD,
    )
    style.map(
        "Accent.TButton",
        background=[
            ("active", ACCENT_ACTIVE),
            ("pressed", ACCENT_PRESSED),
            ("disabled", "#94a3b8"),
        ],
        foreground=[("disabled", "#e2e8f0")],
        bordercolor=[
            ("active", ACCENT_ACTIVE),
            ("pressed", ACCENT_PRESSED),
        ],
    )

    style.configure(
        "Secondary.TButton",
        background=SECONDARY,
        foreground="#ffffff",
        bordercolor=SECONDARY,
        lightcolor=SECONDARY,
        darkcolor="#1e293b",
        focuscolor=SECONDARY_ACTIVE,
        padding=(12, 7),
        font=FONT_UI,
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", SECONDARY_ACTIVE),
            ("pressed", "#1e293b"),
            ("disabled", "#94a3b8"),
        ],
        foreground=[("disabled", "#e2e8f0")],
        bordercolor=[
            ("active", SECONDARY_ACTIVE),
            ("pressed", "#1e293b"),
        ],
    )

    style.configure(
        "Quiet.TButton",
        background=BG,
        foreground=MUTED,
        bordercolor=BORDER,
        lightcolor=BG,
        darkcolor=BORDER,
        padding=(12, 6),
        font=FONT_UI,
    )
    style.map(
        "Quiet.TButton",
        background=[("active", "#e2e8f0"), ("pressed", "#cbd5e1")],
        foreground=[("active", FG)],
    )

    style.configure(
        "TProgressbar",
        troughcolor=PROGRESS_TROUGH,
        background=ACCENT,
        bordercolor=BORDER,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=14,
    )

    style.configure(
        "TSpinbox",
        fieldbackground="#ffffff",
        foreground=FG,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        arrowsize=12,
        padding=3,
    )
    style.configure(
        "TScrollbar",
        background="#c5cede",
        troughcolor=BG,
        bordercolor=BG,
        arrowcolor=FG,
        relief="flat",
    )
    style.map(
        "TScrollbar",
        background=[("active", MUTED), ("pressed", SECONDARY)],
    )

    return style
