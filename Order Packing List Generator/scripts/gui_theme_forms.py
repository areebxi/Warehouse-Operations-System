"""Scrollable form, log text, and message dialog helpers."""

from __future__ import annotations

from tkinter import BOTH, DISABLED, LEFT, RIGHT, X, Y, Canvas, Listbox, Text, Toplevel, ttk

from scripts.gui_theme_palette import _BG
from scripts.gui_theme_widgets import style_log_text


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


def show_scrollable_message(
    parent, title: str, message: str, *, width: int = 560, height: int = 360
) -> None:
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
