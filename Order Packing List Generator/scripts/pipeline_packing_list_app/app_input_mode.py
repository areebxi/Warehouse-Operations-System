from __future__ import annotations

from tkinter import DISABLED, NORMAL

from scripts.gui_theme import set_listbox_enabled, set_tag_chip_grid_enabled

from .ui import on_fixed_process_toggle, on_separate_by_logo_toggle


class PackingListInputModeMixin:
    def _on_fixed_process_toggle(self, *args: object) -> None:
        on_fixed_process_toggle(self, *args)

    def _on_separate_by_logo_toggle(self, *args: object) -> None:
        on_separate_by_logo_toggle(self, *args)

    def _on_missing_pipeline_toggle(self, *args: object) -> None:
        if self.run_missing_logo_pipeline_var.get():
            self.input_mode_var.set("file")
        self._sync_input_mode()

    def _on_input_mode_changed(self, *args: object) -> None:
        self._sync_input_mode()
        if self.is_tag_mode() and not self._shipstation_tags and not self._tags_loading:
            self._refresh_shipstation_tags()

    def _set_tag_controls_enabled(self, enabled: bool, *, loading: bool = False) -> None:
        state_cb = "readonly" if enabled else DISABLED
        btn_state = DISABLED if (not enabled or loading) else NORMAL
        if hasattr(self, "tag_cb"):
            self.tag_cb.config(state=state_cb)
        if hasattr(self, "add_tag_btn"):
            self.add_tag_btn.config(state=btn_state)
        if hasattr(self, "refresh_tags_btn"):
            self.refresh_tags_btn.config(state=btn_state)
        if hasattr(self, "remove_all_tags_btn"):
            self.remove_all_tags_btn.config(state=btn_state)
        if hasattr(self, "tag_chips_frame"):
            set_tag_chip_grid_enabled(self.tag_chips_frame, bool(enabled) and not loading)

    def _set_file_controls_enabled(self, enabled: bool) -> None:
        btn_state = NORMAL if enabled else DISABLED
        for attr in ("add_files_btn", "remove_selected_btn", "remove_all_btn"):
            if hasattr(self, attr):
                getattr(self, attr).config(state=btn_state)
        if hasattr(self, "input_listbox"):
            set_listbox_enabled(self.input_listbox, bool(enabled))

    def _sync_input_mode(self) -> None:
        """Enable/disable tag vs CSV controls from the Input source radios."""
        missing = self.run_missing_logo_pipeline_var.get()
        tag_mode = self.is_tag_mode()
        loading = bool(getattr(self, "_tags_loading", False))

        if hasattr(self, "input_mode_file_rb"):
            self.input_mode_file_rb.config(state=NORMAL)
        if hasattr(self, "input_mode_tag_rb"):
            # Missing pipeline is file-only.
            self.input_mode_tag_rb.config(state=DISABLED if missing else NORMAL)

        if tag_mode:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="TLabel")
            if hasattr(self, "input_label"):
                self.input_label.configure(style="Muted.TLabel")
            self._set_tag_controls_enabled(True, loading=loading)
            self._set_file_controls_enabled(False)
            self.use_fixed_process_number_var.set(True)
            if hasattr(self, "use_fixed_process_cb"):
                self.use_fixed_process_cb.config(state=DISABLED)
            self._update_process_entry_for_tags()
        else:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="Muted.TLabel")
            if hasattr(self, "input_label"):
                self.input_label.configure(style="TLabel")
            self._set_tag_controls_enabled(False)
            self._set_file_controls_enabled(True)
            if hasattr(self, "use_fixed_process_cb"):
                self.use_fixed_process_cb.config(state=NORMAL)
            # Refresh fixed-process entry state for file mode.
            on_fixed_process_toggle(self)
