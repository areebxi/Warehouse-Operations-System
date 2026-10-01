from tkinter import DISABLED, END, NORMAL, messagebox

from scripts.gui_theme import (
    refresh_tag_chip_grid,
    set_listbox_enabled,
    set_tag_chip_grid_enabled,
)
from pipeline_shipstation.tags_process_lookup import lookup_process_number


class PreflightTagsControlsMixin:

    def is_tag_mode(self) -> bool:
        return (self.input_mode_var.get() or "").strip() == "tag"


    def selected_shipstation_tags(self) -> list[tuple[int, str]]:
        return list(self.selected_tags)


    def selected_shipstation_tag(self) -> tuple[int, str] | None:
        tags = self.selected_shipstation_tags()
        return tags[0] if len(tags) == 1 else None


    def _refresh_tag_chips(self) -> None:
        if not hasattr(self, "tag_chips_frame"):
            return
        enabled = self.is_tag_mode() and not getattr(self, "_tags_loading", False)
        refresh_tag_chip_grid(
            self.tag_chips_frame,
            self.selected_tags,
            self._remove_tag_by_id if enabled else None,
            enabled=enabled,
        )


    def _update_process_entry_for_tags(self) -> None:
        if not hasattr(self, "process_entry"):
            return
        # File mode: unused (CSV stem is Process Number). Tag mode: enabled for
        # one tag, disabled when multiple tags (each uses Tags.xlsx).
        if not self.is_tag_mode():
            self.process_entry.config(state=DISABLED)
            if hasattr(self, "process_label"):
                self.process_label.configure(style="Muted.TLabel")
            return
        if hasattr(self, "process_label"):
            self.process_label.configure(style="TLabel")
        multi = len(self.selected_tags) > 1
        self.process_entry.config(state=DISABLED if multi else NORMAL)
        if not multi:
            self._soft_fill_process_from_tags_sheet()


    def _enter_tag_mode_clearing_files(self) -> None:
        self.input_mode_var.set("tag")
        self._syncing_inputs = True
        try:
            self.input_paths.clear()
            if hasattr(self, "listbox"):
                self.listbox.delete(0, END)
        finally:
            self._syncing_inputs = False


    def _add_selected_tag(self) -> None:
        if not self.is_tag_mode():
            return
        name = (self.shipstation_tag_var.get() or "").strip()
        if not name:
            return
        tag_id: int | None = None
        for t in self._shipstation_tags:
            if str(t.get("name") or "") == name:
                try:
                    tag_id = int(t.get("tagId"))
                except (TypeError, ValueError):
                    tag_id = None
                break
        if tag_id is None:
            messagebox.showwarning("ShipStation tags", f"Could not resolve tag id for '{name}'.")
            return
        if any(existing_id == tag_id for existing_id, _ in self.selected_tags):
            return
        self.selected_tags.append((tag_id, name))
        self._enter_tag_mode_clearing_files()
        self._refresh_tag_chips()
        self._update_process_entry_for_tags()
        self._sync_input_mode()


    def _remove_tag_by_id(self, tag_id: int) -> None:
        if not self.is_tag_mode():
            return
        self.selected_tags = [(tid, name) for tid, name in self.selected_tags if tid != tag_id]
        self._refresh_tag_chips()
        self._update_process_entry_for_tags()
        self._sync_input_mode()


    def _remove_all_tags(self) -> None:
        if not self.is_tag_mode():
            return
        self.selected_tags.clear()
        self._refresh_tag_chips()
        self._update_process_entry_for_tags()
        self._sync_input_mode()


    def _on_input_mode_changed(self, *args: object) -> None:
        self._sync_input_mode()
        if self.is_tag_mode() and not self._shipstation_tags and not self._tags_loading:
            self._refresh_shipstation_tags()


    def _on_shift_changed(self, *args: object) -> None:
        self._soft_fill_process_from_tags_sheet()


    def _soft_fill_process_from_tags_sheet(self) -> None:
        """If process is empty with exactly one tag, prefill from ShipStation Tags.xlsx."""
        if not self.is_tag_mode():
            return
        if len(self.selected_tags) != 1:
            return
        if (self.process_number_var.get() or "").strip():
            return
        tag_id, tag_name = self.selected_tags[0]
        shift = (self.shift_var.get() or "").strip()
        if not shift:
            return
        try:
            found = lookup_process_number(
                tag_id=tag_id, tag_name=tag_name, shift_label=shift
            )
        except Exception:
            return
        if found:
            self.process_number_var.set(found)


    def _set_tag_controls_enabled(self, enabled: bool, *, loading: bool = False) -> None:
        state_cb = "readonly" if enabled else DISABLED
        btn_state = DISABLED if (not enabled or loading) else NORMAL
        if hasattr(self, "tag_cb"):
            self.tag_cb.config(state=state_cb)
        for attr in ("add_tag_btn", "refresh_tags_btn", "remove_all_tags_btn"):
            if hasattr(self, attr):
                getattr(self, attr).config(state=btn_state)
        if hasattr(self, "tag_chips_frame"):
            set_tag_chip_grid_enabled(self.tag_chips_frame, bool(enabled) and not loading)


    def _sync_input_mode(self) -> None:
        tag_mode = self.is_tag_mode()
        loading = bool(getattr(self, "_tags_loading", False))
        if tag_mode:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="TLabel")
            if hasattr(self, "input_files_label"):
                self.input_files_label.configure(style="Muted.TLabel")
            self._set_tag_controls_enabled(True, loading=loading)
            self.add_files_btn.config(state=DISABLED)
            self.remove_selected_btn.config(state=DISABLED)
            self.remove_all_btn.config(state=DISABLED)
            set_listbox_enabled(self.listbox, False)
            self.date_entry.config(state=NORMAL)
            self.shift_cb.config(state="readonly")
            self._update_process_entry_for_tags()
        else:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="Muted.TLabel")
            if hasattr(self, "input_files_label"):
                self.input_files_label.configure(style="TLabel")
            self._set_tag_controls_enabled(False)
            self.add_files_btn.config(state=NORMAL)
            self.remove_selected_btn.config(state=NORMAL)
            self.remove_all_btn.config(state=NORMAL)
            set_listbox_enabled(self.listbox, True)
            self.date_entry.config(state=NORMAL)
            self.shift_cb.config(state="readonly")
            self._update_process_entry_for_tags()

