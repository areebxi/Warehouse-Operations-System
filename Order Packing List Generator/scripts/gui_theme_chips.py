"""Tag chip grid helpers for packing GUIs."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from tkinter import DISABLED, NORMAL, ttk


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
