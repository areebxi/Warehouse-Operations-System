from __future__ import annotations
import unittest
from pathlib import Path
from scripts.pipeline_generate_packing_list_pdf.back_print_hint import (
    label_for_logo_slot,
    label_from_stem_after_anchor,
    logo_filename_indicates_back,
    resolve_apparel_logo_anchor,
    resolve_logo_anchor_for_slot,
    slot_is_back_print,
    strip_side_suffix_from_token,
)

class SlotIsBackPrintTests(unittest.TestCase):
    def _row(self, **fields):
        class Row:
            def get(self, key, default=None):
                return fields.get(key, default)

        return Row()

    def _slot_is_back(self, slot_index, img_path, row, **kwargs):
        defaults = {
            "fbpi_slots": [],
            "position_code_to_draw": None,
            "default_position_code": "X",
            "safe_str": lambda v: str(v or "").strip(),
            "position_tokens": lambda v: [t.strip() for t in str(v or "").split(",") if t.strip()][:5],
            "logo_design_tokens": lambda v: [t.strip() for t in str(v or "").split(",") if t.strip()][:5],
        }
        defaults.update(kwargs)
        return slot_is_back_print(slot_index, img_path, row_series=row, **defaults)

    def test_position_back_no_slash_slot_zero(self):
        row = self._row(Position="Back", **{"Logo/Design Image": "103671LG"})
        self.assertTrue(self._slot_is_back(0, Path("logo.png"), row))

    def test_position_front_comma_back_slot_mapping(self):
        row = self._row(Position="Front, Back", **{"Logo/Design Image": "103671LG-f, 103671LG-b"})
        self.assertFalse(self._slot_is_back(0, Path("front.png"), row))
        self.assertTrue(self._slot_is_back(1, Path("back.png"), row))

    def test_position_slash_disables_position_trigger(self):
        row = self._row(Position="Pocket / Back", **{"Logo/Design Image": "62351LG"})
        self.assertFalse(self._slot_is_back(0, Path("logo.png"), row))

    def test_filename_still_triggers_when_position_has_slash(self):
        row = self._row(
            Position="Pocket / Back",
            **{"Logo/Design Image": "202-3246136-6506730-13"},
        )
        img = Path("202-3246136-6506730-13-b-98765PER.png")
        self.assertTrue(self._slot_is_back(0, img, row))

    def test_no_img_path_returns_false(self):
        row = self._row(Position="Back", **{"Logo/Design Image": "103671LG"})
        self.assertFalse(self._slot_is_back(0, None, row))

    def test_position_code_workbook_lookup(self):
        row = self._row(
            Position="",
            **{"Position Code": "X015", "Logo/Design Image": "62351LG"},
        )
        position_code_to_draw = {"X015": "Pocket, Back"}
        self.assertFalse(
            self._slot_is_back(
                0,
                Path("logo.png"),
                row,
                position_code_to_draw=position_code_to_draw,
            )
        )
        self.assertTrue(
            self._slot_is_back(
                1,
                Path("logo.png"),
                row,
                position_code_to_draw=position_code_to_draw,
            )
        )
