import json
import sys
from pathlib import Path
from tkinter import END

from pipeline_shipstation.tags_process_lookup import (
    parse_shipstation_tags_config,
    shipstation_tags_config_payload,
)

from .config import CONFIG_DIR, PREFLIGHT_CONFIG, PROJECT_ROOT, UNMATCHED_CONFIG


class PreflightConfigMixin:

    def _load_config(self) -> None:
        path_candidates = [
            PREFLIGHT_CONFIG,
            UNMATCHED_CONFIG,
            PROJECT_ROOT / "preflight_issues_config.json",
            PROJECT_ROOT / "unmatched_skus_config.json",
        ]
        data: dict | None = None
        for path in path_candidates:
            if not path.is_file():
                continue
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
                    break
            except Exception:
                continue
        if data is None:
            return
        # ponytail: never restore date — always open as today (field stays editable)
        mapping = {
            "workbook_path": self.workbook_var,
            "cl_csv_path": self.cl_csv_var,
            "output_dir": self.output_dir_var,
            "apparel_dir": self.apparel_dir_var,
            "logo_normal_dir": self.logo_normal_dir_var,
            "logo_custom_single_dir": self.logo_custom_single_dir_var,
            "logo_custom_double_dir": self.logo_custom_double_dir_var,
            "shift": self.shift_var,
            "process_number": self.process_number_var,
        }
        for key, var in mapping.items():
            val = str(data.get(key, "")).strip()
            if val:
                var.set(val)
        mode = str(data.get("input_mode", "")).strip().lower()
        self.input_mode_var.set("tag" if mode == "tag" else "file")
        self.selected_tags = parse_shipstation_tags_config(data)
        self.input_paths = self._parse_saved_input_files(data)
        if isinstance(data.get("use_demo_images"), bool):
            self.use_demo_images_var.set(data["use_demo_images"])


    def _parse_saved_input_files(data: dict) -> list[Path]:
        raw = data.get("input_files")
        paths: list[Path] = []
        if isinstance(raw, list):
            for item in raw:
                text = str(item or "").strip()
                if not text:
                    continue
                path = Path(text)
                if path.is_file() and path not in paths:
                    paths.append(path)
        elif isinstance(raw, str) and raw.strip():
            # Legacy / accidental single-string form
            path = Path(raw.strip())
            if path.is_file():
                paths.append(path)
        return paths


    def _refresh_input_listbox(self) -> None:
        if not hasattr(self, "listbox"):
            return
        self.listbox.delete(0, END)
        for path in self.input_paths:
            self.listbox.insert(END, str(path))


    def _save_config(self) -> None:
        tags_payload, legacy_name, legacy_id = shipstation_tags_config_payload(self.selected_tags)
        data = {
            "workbook_path": (self.workbook_var.get() or "").strip(),
            "cl_csv_path": (self.cl_csv_var.get() or "").strip(),
            "output_dir": (self.output_dir_var.get() or "").strip(),
            "apparel_dir": (self.apparel_dir_var.get() or "").strip(),
            "logo_normal_dir": (self.logo_normal_dir_var.get() or "").strip(),
            "logo_custom_single_dir": (self.logo_custom_single_dir_var.get() or "").strip(),
            "logo_custom_double_dir": (self.logo_custom_double_dir_var.get() or "").strip(),
            "use_demo_images": self.use_demo_images_var.get(),
            "date": (self.date_var.get() or "").strip(),
            "shift": (self.shift_var.get() or "").strip(),
            "process_number": (self.process_number_var.get() or "").strip(),
            "input_mode": "tag" if (self.input_mode_var.get() or "").strip() == "tag" else "file",
            "input_files": [str(p) for p in self.input_paths],
            "shipstation_tags": tags_payload,
            "shipstation_tag_name": legacy_name,
            "shipstation_tag_id": legacy_id,
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            PREFLIGHT_CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(
                f"[preflight issues] config save failed ({PREFLIGHT_CONFIG}): {exc}",
                file=sys.stderr,
                flush=True,
            )


    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()

