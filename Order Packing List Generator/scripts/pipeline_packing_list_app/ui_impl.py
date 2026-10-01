from __future__ import annotations
from tkinter import DISABLED, NORMAL, Listbox, MULTIPLE, ttk
from scripts.gui_theme import make_log_text, make_scrollable_form, style_listbox

def on_fixed_process_toggle(app, *args: object) -> None:

    # Tag mode keeps fixed process enabled; multi-tag disables the entry.

    if getattr(app, "is_tag_mode", lambda: False)():

        app.use_fixed_process_number_var.set(True)

        multi = len(getattr(app, "selected_tags", []) or []) > 1

        if hasattr(app, "fixed_process_entry"):

            app.fixed_process_entry.config(state=DISABLED if multi else NORMAL)

        if hasattr(app, "use_fixed_process_cb"):

            app.use_fixed_process_cb.config(state=DISABLED)

        return

    if hasattr(app, "use_fixed_process_cb"):

        app.use_fixed_process_cb.config(state=NORMAL)

    if app.use_fixed_process_number_var.get():

        app.fixed_process_entry.config(state=NORMAL)

    else:

        app.fixed_process_number_var.set("")

        app.fixed_process_entry.config(state=DISABLED)
def on_separate_by_logo_toggle(app, *args: object) -> None:

    app.logo_id_threshold_entry.config(state=NORMAL if app.separate_by_logo_id_var.get() else DISABLED)
