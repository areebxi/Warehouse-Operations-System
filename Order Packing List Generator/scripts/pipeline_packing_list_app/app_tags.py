from __future__ import annotations

import threading
from tkinter import DISABLED, NORMAL, messagebox

from scripts.gui_theme import refresh_tag_chip_grid
from pipeline_shipstation.client import ShipStationClient
from pipeline_shipstation.credentials import load_shipstation_credentials
from pipeline_shipstation.tags_process_lookup import lookup_process_number


class PackingListTagsMixin:
    def is_tag_mode(self) -> bool:
        """True when ShipStation tag is the selected input source (not missing pipeline)."""
        if self.run_missing_logo_pipeline_var.get():
            return False
        return (self.input_mode_var.get() or "").strip() == "tag"

    def selected_shipstation_tags(self) -> list[tuple[int, str]]:
        """Return selected (tagId, name) pairs."""
        return list(self.selected_tags)

    def selected_shipstation_tag(self) -> tuple[int, str] | None:
        """Return the sole selected tag, or None if zero/multiple."""
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
        """Disable fixed process when multiple tags are selected."""
        if not self.is_tag_mode():
            return
        multi = len(self.selected_tags) > 1
        if hasattr(self, "fixed_process_entry"):
            self.fixed_process_entry.config(state=DISABLED if multi else NORMAL)
        if multi:
            # Soft-fill does not apply; leave any leftover value unused.
            return
        self._soft_fill_process_from_tags_sheet()

    def _enter_tag_mode_clearing_csv(self) -> None:
        if self.run_missing_logo_pipeline_var.get():
            return
        self.input_mode_var.set("tag")
        self.input_paths.clear()
        self._sync_input_var_from_paths()
        self._refresh_input_listbox()

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
        self._enter_tag_mode_clearing_csv()
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

    def _on_shift_changed(self, *args: object) -> None:
        self._soft_fill_process_from_tags_sheet()

    def _soft_fill_process_from_tags_sheet(self) -> None:
        """If process is empty with exactly one tag, prefill from ShipStation Tags.xlsx."""
        if not self.is_tag_mode():
            return
        if len(self.selected_tags) != 1:
            return
        if (self.fixed_process_number_var.get() or "").strip():
            return
        tag_id, tag_name = self.selected_tags[0]
        shift = (self.shift_var.get() or "").strip()
        if not shift:
            return
        try:
            found = lookup_process_number(
                tag_id=tag_id,
                tag_name=tag_name,
                shift_label=shift,
            )
        except Exception:
            return
        if found:
            self.fixed_process_number_var.set(found)

    def _refresh_shipstation_tags(self) -> None:
        """Load tags from ShipStation on a background thread."""
        if not self.is_tag_mode():
            return
        if getattr(self, "_tags_loading", False):
            return
        self._tags_loading = True
        self._sync_input_mode()

        def worker() -> None:
            try:
                client = ShipStationClient(load_shipstation_credentials())
                tags = client.list_tags()
                self.root.after(0, self._on_tags_loaded, tags, None)
            except Exception as exc:
                self.root.after(0, self._on_tags_loaded, [], str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_tags_loaded(self, tags: list, error: str | None) -> None:
        self._tags_loading = False
        self._shipstation_tags = tags or []
        names = [str(t.get("name") or "") for t in self._shipstation_tags]
        if hasattr(self, "tag_cb"):
            self.tag_cb["values"] = names

        # Refresh selected list names from API when ids still exist.
        refreshed: list[tuple[int, str]] = []
        by_id = {}
        for t in self._shipstation_tags:
            try:
                by_id[int(t.get("tagId"))] = str(t.get("name") or "")
            except (TypeError, ValueError):
                continue
        for tag_id, name in self.selected_tags:
            if tag_id in by_id:
                refreshed.append((tag_id, by_id[tag_id] or name))
            else:
                # Keep saved selection even if temporarily missing from API.
                refreshed.append((tag_id, name))
        self.selected_tags = refreshed
        self._refresh_tag_chips()

        # Keep combobox on a sensible pick value.
        current_pick = (self.shipstation_tag_var.get() or "").strip()
        if current_pick and current_pick not in names:
            self.shipstation_tag_var.set("")
        elif not current_pick and names:
            self.shipstation_tag_var.set(names[0])

        self._sync_input_mode()
        if error:
            messagebox.showwarning("ShipStation tags", f"Could not load tags:\n{error}")
