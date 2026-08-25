"""Shared ttk theme for Packing List, Missing Run, and Preflight Issues apps.

Applies once at startup — zero runtime cost after that.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from tkinter import BOTH, DISABLED, LEFT, RIGHT, X, Y, Canvas, Listbox, NORMAL, Text, Tk, Toplevel, ttk

# Cool slate + teal accent — clean ops-tool look, not default gray.
_BG = "#EEF2F6"
_SURFACE = "#FFFFFF"
_TEXT = "#1E293B"
_MUTED = "#64748B"
_BORDER = "#CBD5E1"
_ACCENT = "#0F766E"
_ACCENT_HOVER = "#0D9488"
_ACCENT_ACTIVE = "#115E59"
_ACCENT_FG = "#FFFFFF"
_LOG_BG = "#F8FAFC"
_LOG_FG = "#334155"
_SELECT_BG = "#CCFBF1"
_SELECT_FG = "#134E4A"
_DISABLED_BG = "#E2E8F0"
_DISABLED_FG = "#94A3B8"

_FONT_UI = ("Segoe UI", 10)
_FONT_UI_BOLD = ("Segoe UI", 10, "bold")
_FONT_TITLE = ("Segoe UI", 14, "bold")
_FONT_LOG = ("Consolas", 9)


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
        fieldbackground=[
            ("disabled", _DISABLED_BG),
            ("readonly", _SURFACE),
        ],
        background=[
            ("disabled", _DISABLED_BG),
            ("readonly", _SURFACE),
        ],
        foreground=[("disabled", _DISABLED_FG)],
        arrowcolor=[("disabled", _DISABLED_FG)],
        selectbackground=[
            ("disabled", _DISABLED_BG),
            ("readonly", _SELECT_BG),
        ],
        selectforeground=[
            ("disabled", _DISABLED_FG),
            ("readonly", _SELECT_FG),
        ],
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

    return style


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


def refresh_tag_chip_grid(
    container: ttk.Frame,
    tags: Sequence[tuple[int, str]],
    on_remove: Callable[[int], None] | None,
    *,
    enabled: bool = True,
) -> None:
    """Lay out selected tags as wrapping chips; click × (chip) to remove one."""
    container._chip_data = [(int(tag_id), str(name or "")) for tag_id, name in tags]
    container._chip_on_remove = on_remove
    container._chip_enabled = bool(enabled)
    container._chip_sig = None
    if not getattr(container, "_chip_bound", False):
        container.bind("<Configure>", lambda _e, c=container: _reflow_tag_chips(c))
        container._chip_bound = True
    _reflow_tag_chips(container)


def set_tag_chip_grid_enabled(container: ttk.Frame, enabled: bool) -> None:
    """Enable/disable chip clicks without changing the tag list."""
    tags = getattr(container, "_chip_data", []) or []
    on_remove = getattr(container, "_chip_on_remove", None)
    refresh_tag_chip_grid(container, tags, on_remove, enabled=enabled)


def _reflow_tag_chips(container: ttk.Frame) -> None:
    if getattr(container, "_chip_busy", False):
        return

    tags: list[tuple[int, str]] = list(getattr(container, "_chip_data", []) or [])
    on_remove = getattr(container, "_chip_on_remove", None)
    enabled = bool(getattr(container, "_chip_enabled", True))

    avail = int(container.winfo_width() or 0)
    if avail < 80:
        try:
            avail = max(int(container.master.winfo_width()) - 24, 400)
        except Exception:
            avail = 400

    data_sig = (tuple(tags), enabled, avail)
    if data_sig == getattr(container, "_chip_sig", None) and container.winfo_children():
        return

    container._chip_busy = True
    try:
        for child in container.winfo_children():
            child.destroy()

        if not tags:
            ttk.Label(container, text="(none selected)", style="Muted.TLabel").grid(
                row=0, column=0, sticky="w", pady=2
            )
            container._chip_sig = data_sig
            return

        row = 0
        col = 0
        x = 0
        pad_x = 4
        for tag_id, name in tags:
            display = name.strip() or str(tag_id)
            text = f"{display}  ×"

            def _make_cmd(tid: int = tag_id) -> Callable[[], None] | None:
                if not enabled or on_remove is None:
                    return None

                def _cmd() -> None:
                    on_remove(tid)

                return _cmd

            btn = ttk.Button(
                container,
                text=text,
                style="Chip.TButton",
                command=_make_cmd(),
                state=NORMAL if enabled else DISABLED,
            )
            btn.update_idletasks()
            bw = max(btn.winfo_reqwidth(), 1) + pad_x
            if col > 0 and x + bw > avail:
                row += 1
                col = 0
                x = 0
            btn.grid(row=row, column=col, padx=(0, pad_x), pady=(0, 4), sticky="w")
            x += bw
            col += 1
        container._chip_sig = data_sig
    finally:
        container._chip_busy = False


def make_scrollable_form(parent) -> tuple[ttk.Frame, ttk.Frame]:
    """Return (container, form_frame) for a mouse-wheel-scrollable config area.

    Pack ``container`` into the parent; put all config widgets on ``form_frame``.
    Nested Listbox/Text widgets keep their own scrolling when hovered.
    """
    container = ttk.Frame(parent)
    canvas = Canvas(container, highlightthickness=0, bg=_BG, bd=0)
    vscroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    form_frame = ttk.Frame(canvas, padding=(0, 0, 8, 0))

    canvas.configure(yscrollcommand=vscroll.set)
    vscroll.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    window_id = canvas.create_window((0, 0), window=form_frame, anchor="nw")

    def _sync_scrollregion(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _sync_width(event) -> None:
        canvas.itemconfigure(window_id, width=event.width)

    form_frame.bind("<Configure>", _sync_scrollregion)
    canvas.bind("<Configure>", _sync_width)

    def _wheel_target_is_nested(widget) -> bool:
        while widget is not None:
            if isinstance(widget, (Listbox, Text, Canvas)) and widget is not canvas:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _on_mousewheel(event) -> str | None:
        try:
            under = canvas.winfo_containing(event.x_root, event.y_root)
        except Exception:
            under = event.widget
        if under is not None and _wheel_target_is_nested(under):
            return None
        # Only scroll when pointer is over this scroll area.
        w = under
        while w is not None:
            if w is container or w is canvas or w is form_frame:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            w = getattr(w, "master", None)
        return None

    def _bind_wheel(_event=None) -> None:
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_wheel(_event=None) -> None:
        canvas.unbind_all("<MouseWheel>")

    container.bind("<Enter>", _bind_wheel)
    container.bind("<Leave>", _unbind_wheel)
    canvas.bind("<Destroy>", _unbind_wheel)

    return container, form_frame


def make_log_text(parent, *, height: int = 8) -> Text:
    """Build a themed log Text with a vertical scrollbar. Returns the Text widget."""
    frame = ttk.Frame(parent)
    frame.pack(fill=BOTH, expand=True)
    log = Text(frame, height=height, wrap="word")
    style_log_text(log)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=log.yview)
    log.configure(yscrollcommand=scroll.set)
    scroll.pack(side=RIGHT, fill=Y)
    log.pack(side=LEFT, fill=BOTH, expand=True)
    return log


def show_scrollable_message(parent, title: str, message: str, *, width: int = 560, height: int = 360) -> None:
    """Modal dialog with a scrollable body — safe for long finished/error summaries."""
    dialog = Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.configure(bg=_BG)
    dialog.resizable(True, True)

    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()
    max_w = max(360, min(width, int(screen_w * 0.85)))
    max_h = max(240, min(height, int(screen_h * 0.7)))
    dialog.minsize(360, 220)

    outer = ttk.Frame(dialog, padding=14)
    outer.pack(fill=BOTH, expand=True)

    body = ttk.Frame(outer)
    body.pack(fill=BOTH, expand=True)

    text = Text(body, wrap="word", height=12)
    style_log_text(text)
    scroll = ttk.Scrollbar(body, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    scroll.pack(side=RIGHT, fill=Y)
    text.pack(side=LEFT, fill=BOTH, expand=True)
    text.insert("1.0", message)
    text.configure(state=DISABLED)

    btn_row = ttk.Frame(outer)
    btn_row.pack(fill=X, pady=(12, 0))

    def _close() -> None:
        dialog.grab_release()
        dialog.destroy()

    ok_btn = ttk.Button(btn_row, text="OK", style="Accent.TButton", command=_close)
    ok_btn.pack(side=RIGHT)
    dialog.bind("<Return>", lambda _e: _close())
    dialog.bind("<Escape>", lambda _e: _close())
    dialog.protocol("WM_DELETE_WINDOW", _close)

    dialog.update_idletasks()
    # Size to content up to the screen-capped max, then center on parent.
    req_w = min(max_w, max(360, dialog.winfo_reqwidth()))
    req_h = min(max_h, max(220, dialog.winfo_reqheight()))
    # Prefer the intended viewport when content is long.
    line_count = max(1, message.count("\n") + 1)
    if line_count > 12 or len(message) > 400:
        req_w = max_w
        req_h = max_h

    try:
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + max(0, (pw - req_w) // 2)
        y = py + max(0, (ph - req_h) // 2)
    except Exception:
        x = max(0, (screen_w - req_w) // 2)
        y = max(0, (screen_h - req_h) // 2)

    dialog.geometry(f"{req_w}x{req_h}+{x}+{y}")
    dialog.grab_set()
    ok_btn.focus_set()
    dialog.wait_window()
