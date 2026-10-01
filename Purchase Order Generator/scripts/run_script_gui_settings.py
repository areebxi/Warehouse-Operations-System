"""PO GUI settings + ShipStation tag mapping."""

from __future__ import annotations

import json
import os

import openpyxl

from app_paths import DATA_DIR, shipstation_tags_path

GUI_SETTINGS_PATH = DATA_DIR / "gui_settings.json"


def load_gui_settings() -> dict:
    """Load remembered GUI settings (e.g. PDF copy folder)."""
    try:
        if GUI_SETTINGS_PATH.exists():
            with open(GUI_SETTINGS_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"[WARNING] Could not load GUI settings: {e}")
    return {}


def save_gui_settings(settings: dict) -> None:
    """Persist GUI settings to data/gui_settings.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(GUI_SETTINGS_PATH, "w", encoding="utf-8") as handle:
            json.dump(settings, handle, indent=2)
    except Exception as e:
        print(f"[WARNING] Could not save GUI settings: {e}")


def load_tag_mapping():
    """
    Load Tag Name → Tag ID from ShipStation Tags.xlsx.
    Column B: Tag Name, Column C: Tag ID
    """
    tag_mapping = {}
    try:
        xlsx_path = str(shipstation_tags_path())
        if not os.path.exists(xlsx_path):
            print(f"[WARNING] ShipStation Tags.xlsx not found at: {xlsx_path}")
            return tag_mapping

        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=2):  # Skip header row
            tag_name_cell = row[1]  # Column B (0-based index 1)
            tag_id_cell = row[2]  # Column C (0-based index 2)

            tag_name = "" if tag_name_cell.value is None else str(tag_name_cell.value).strip()
            tag_id = "" if tag_id_cell.value is None else str(tag_id_cell.value).strip()

            if tag_name and tag_id:
                tag_mapping[tag_name] = tag_id

        return tag_mapping
    except Exception as e:
        print(f"[ERROR] Error loading tag mapping: {e}")
        return tag_mapping
