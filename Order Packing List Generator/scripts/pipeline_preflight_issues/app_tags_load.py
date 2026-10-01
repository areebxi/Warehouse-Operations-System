import threading
from tkinter import messagebox

from pipeline_shipstation.client import ShipStationClient
from pipeline_shipstation.credentials import load_shipstation_credentials


class PreflightTagsLoadMixin:

    def _refresh_shipstation_tags(self) -> None:
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
        self.tag_cb["values"] = names

        by_id: dict[int, str] = {}
        for t in self._shipstation_tags:
            try:
                by_id[int(t.get("tagId"))] = str(t.get("name") or "")
            except (TypeError, ValueError):
                continue
        refreshed: list[tuple[int, str]] = []
        for tag_id, name in self.selected_tags:
            if tag_id in by_id:
                refreshed.append((tag_id, by_id[tag_id] or name))
            else:
                refreshed.append((tag_id, name))
        self.selected_tags = refreshed
        self._refresh_tag_chips()

        current_pick = (self.shipstation_tag_var.get() or "").strip()
        if current_pick and current_pick not in names:
            self.shipstation_tag_var.set("")
        elif not current_pick and names:
            self.shipstation_tag_var.set(names[0])

        self._sync_input_mode()
        if error:
            messagebox.showwarning("ShipStation tags", f"Could not load tags:\n{error}")

