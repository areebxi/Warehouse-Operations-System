from __future__ import annotations
from pathlib import Path
from typing import Any
from openpyxl import load_workbook
from .sync_tags_xlsx import DEFAULT_XLSX_PATH, SHEET_NAME, _as_int, _name_key

def parse_shipstation_tags_config(data: dict) -> list[tuple[int, str]]:
    """Load selected tags from config; prefer ``shipstation_tags``, else legacy scalars."""
    raw = data.get("shipstation_tags")
    out: list[tuple[int, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                tag_id = int(item.get("id"))
            except (TypeError, ValueError):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            if any(existing_id == tag_id for existing_id, _ in out):
                continue
            out.append((tag_id, name))
        if out:
            return out

    raw_id = str(data.get("shipstation_tag_id") or "").strip()
    name = str(data.get("shipstation_tag_name") or "").strip()
    if raw_id and name:
        try:
            return [(int(raw_id), name)]
        except ValueError:
            return []
    return []
def shipstation_tags_config_payload(
    tags: list[tuple[int, str]],
) -> tuple[list[dict[str, object]], str, str]:
    """Return (shipstation_tags list, legacy name, legacy id) for config save."""
    payload = [{"id": tag_id, "name": name} for tag_id, name in tags]
    if tags:
        first_id, first_name = tags[0]
        return payload, first_name, str(first_id)
    return payload, "", ""
