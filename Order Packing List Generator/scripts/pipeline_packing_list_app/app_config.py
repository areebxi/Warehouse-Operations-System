from __future__ import annotations

import json
import sys

from pipeline_shipstation.tags_process_lookup import (
    parse_shipstation_tags_config,
    shipstation_tags_config_payload,
)

from .config import CONFIG_DIR, CONFIG_KEYS, CONFIG_PATH, PROJECT_ROOT


class PackingListConfigMixin:
    def _load_config(self) -> None:
        data = None
        for path in (CONFIG_PATH, PROJECT_ROOT / "gui_config.json"):
            if not path.exists():
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
        var_map = {
            "input_csv": self.input_csv_var,
            "shift": self.shift_var,
            "output_dir": self.output_dir_var,
            "workbook_path": self.workbook_var,
            "cl_csv_path": self.cl_csv_var,
            "apparel_dir": self.apparel_dir_var,
            "logo_normal_dir": self.logo_normal_dir_var,
            "logo_custom_single_dir": self.logo_custom_single_dir_var,
            "logo_custom_double_dir": self.logo_custom_double_dir_var,
            "pdf_copy_dir": self.pdf_copy_dir_var,
            "excel_copy_dir": self.excel_copy_dir_var,
        }
        for key in CONFIG_KEYS:
            if key not in data:
                continue
            if key == "date":
                continue
            if key == "separate_by_logo_id" and isinstance(data[key], bool):
                self.separate_by_logo_id_var.set(data[key])
            elif key == "logo_id_threshold":
                self.logo_id_threshold_var.set(
                    str(int(data[key])) if str(data[key]).strip().isdigit() else "5"
                )
            elif key == "use_fixed_process_number" and isinstance(data[key], bool):
                self.use_fixed_process_number_var.set(data[key])
            elif key == "fixed_process_number" and isinstance(data[key], str):
                self.fixed_process_number_var.set(data[key])
            elif key == "run_missing_logo_pipeline" and isinstance(data[key], bool):
                self.run_missing_logo_pipeline_var.set(data[key])
            elif key == "use_demo_images" and isinstance(data[key], bool):
                self.use_demo_images_var.set(data[key])
            elif key == "input_mode" and isinstance(data[key], str):
                mode = data[key].strip().lower()
                self.input_mode_var.set("tag" if mode == "tag" else "file")
            elif key in ("shipstation_tag_name", "shipstation_tag_id", "shipstation_tags"):
                continue
            elif isinstance(data[key], str) and key in var_map:
                var_map[key].set(data[key])
        self.selected_tags = parse_shipstation_tags_config(data)

    def _save_config(self) -> None:
        self._sync_input_var_from_paths()
        tags_payload, legacy_name, legacy_id = shipstation_tags_config_payload(self.selected_tags)
        data = {
            "input_csv": self.input_csv_var.get() or "",
            "date": self.date_var.get() or "",
            "shift": self.shift_var.get() or "",
            "output_dir": self.output_dir_var.get() or "",
            "workbook_path": self.workbook_var.get() or "",
            "cl_csv_path": self.cl_csv_var.get() or "",
            "apparel_dir": self.apparel_dir_var.get() or "",
            "logo_normal_dir": self.logo_normal_dir_var.get() or "",
            "logo_custom_single_dir": (self.logo_custom_single_dir_var.get() or "").strip(),
            "logo_custom_double_dir": (self.logo_custom_double_dir_var.get() or "").strip(),
            "pdf_copy_dir": (self.pdf_copy_dir_var.get() or "").strip(),
            "excel_copy_dir": (self.excel_copy_dir_var.get() or "").strip(),
            "separate_by_logo_id": self.separate_by_logo_id_var.get(),
            "logo_id_threshold": (
                int(self.logo_id_threshold_var.get())
                if str(self.logo_id_threshold_var.get()).strip().isdigit()
                else 5
            ),
            "use_fixed_process_number": self.use_fixed_process_number_var.get(),
            "fixed_process_number": (self.fixed_process_number_var.get() or "").strip(),
            "run_missing_logo_pipeline": self.run_missing_logo_pipeline_var.get(),
            "use_demo_images": self.use_demo_images_var.get(),
            "input_mode": "tag" if (self.input_mode_var.get() or "").strip() == "tag" else "file",
            "shipstation_tags": tags_payload,
            "shipstation_tag_name": legacy_name,
            "shipstation_tag_id": legacy_id,
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(
                f"[packing list] config save failed ({CONFIG_PATH}): {exc}",
                file=sys.stderr,
                flush=True,
            )

    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()
