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


class LabelFromStemAfterAnchorTests(unittest.TestCase):
    def test_front_after_order_token(self):
        anchor = "026-0313955-0013102"
        stem = "026-0313955-0013102-f-161890LG-M-T-FUC-L-YES"
        self.assertEqual(label_from_stem_after_anchor(stem, anchor), "Front")

    def test_front_uppercase_f_segment(self):
        anchor = "202-3246136-6506730-13"
        stem = "202-3246136-6506730-13-F-98765PER-M-T-SPH-S-Yes"
        self.assertEqual(label_from_stem_after_anchor(stem, anchor), "Front")

    def test_no_false_sleeve_in_sku_tail(self):
        anchor = "026-0313955-0013102"
        stem = "026-0313955-0013102-161890LG-M-T-FUC-S-YES"
        self.assertIsNone(label_from_stem_after_anchor(stem, anchor))

    def test_step4_token_with_suffix(self):
        self.assertEqual(label_from_stem_after_anchor("103671LG-f", "103671LG-f"), "Front")
        self.assertEqual(label_from_stem_after_anchor("103671LG-b", "103671LG-b"), "Back")

    def test_back_hyphenated_segment(self):
        anchor = "202-3246136-6506730-13"
        stem = "202-3246136-6506730-13-b-98765PER-M-T-SPH-S-Yes"
        self.assertEqual(label_from_stem_after_anchor(stem, anchor), "Back")

    def test_pocket_after_order_token(self):
        anchor = "202-9359504-5073928"
        stem = "202-9359504-5073928-p-98765PER-M-T-SPH-M-Yes"
        self.assertEqual(label_from_stem_after_anchor(stem, anchor), "Pocket")

    def test_sleeve_uppercase_s_segment(self):
        anchor = "202-9359504-5073928"
        stem = "202-9359504-5073928-S-98765PER-M-T-SPH-M-Yes"
        self.assertEqual(label_from_stem_after_anchor(stem, anchor), "Sleeve")

    def test_stem_must_start_with_anchor(self):
        self.assertIsNone(label_from_stem_after_anchor("other-f", "026-0313955-0013102"))

    def test_empty_anchor(self):
        self.assertIsNone(label_from_stem_after_anchor("anything-f", ""))


class ResolveLogoAnchorTests(unittest.TestCase):
    def test_fbpi_uses_stripped_base(self):
        class Row:
            def get(self, key, default=None):
                if key == "Logo/Design Image":
                    return "order-1"
                return default

        anchor = resolve_logo_anchor_for_slot(
            1,
            Row(),
            fbpi_slots=[(None, "Front")],
            logo_design_tokens=lambda _v: ["order-1"],
        )
        self.assertEqual(anchor, "order-1")

    def test_fbpi_base_when_token_already_has_suffix(self):
        class Row:
            def get(self, key, default=None):
                if key == "Logo/Design Image":
                    return "order-1-f, order-1-b"
                return default

        tokens_fn = lambda v: [t.strip() for t in str(v or "").split(",") if t.strip()]
        anchor = resolve_logo_anchor_for_slot(
            2,
            Row(),
            fbpi_slots=[(None, "Front"), (None, "Back")],
            logo_design_tokens=tokens_fn,
        )
        self.assertEqual(anchor, "order-1")

    def test_comma_separated_tokens_without_fbpi(self):
        class Row:
            def get(self, key, default=None):
                if key == "Logo/Design Image":
                    return "103671LG-f, 103671LG-b"
                return default

        tokens_fn = lambda v: [t.strip() for t in str(v or "").split(",") if t.strip()]
        self.assertEqual(
            resolve_logo_anchor_for_slot(0, Row(), fbpi_slots=[], logo_design_tokens=tokens_fn),
            "103671LG-f",
        )
        self.assertEqual(
            resolve_logo_anchor_for_slot(1, Row(), fbpi_slots=[], logo_design_tokens=tokens_fn),
            "103671LG-b",
        )


class LabelForLogoSlotTests(unittest.TestCase):
    def test_fbpi_fallback_when_stem_unusual(self):
        class Row:
            def get(self, key, default=None):
                if key == "Logo/Design Image":
                    return "order-1"
                return default

        label = label_for_logo_slot(
            "unexpected-name-but-back.jpg",
            2,
            Row(),
            fbpi_slots=[(None, "Front"), (None, "Back")],
            logo_design_tokens=lambda _v: ["order-1"],
        )
        self.assertEqual(label, "Back")


class LogoFilenameIndicatesBackTests(unittest.TestCase):
    def test_fbpi_back_without_stem_match(self):
        from pathlib import Path

        self.assertTrue(
            logo_filename_indicates_back(
                Path("x.jpg"),
                anchor_token="order",
                fbpi_side_label="Back",
            )
        )


class StripSideSuffixTests(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(strip_side_suffix_from_token("103671LG-f"), "103671LG")
        self.assertEqual(strip_side_suffix_from_token("order-1"), "order-1")


class ResolveApparelAnchorTests(unittest.TestCase):
    def test_first_logo_token_stripped(self):
        class Row:
            def get(self, key, default=None):
                if key == "Logo/Design Image":
                    return "026-0313955-0013102-f, 026-0313955-0013102-b"
                return default

        anchor = resolve_apparel_logo_anchor(
            Row(),
            logo_design_tokens=lambda v: [t.strip() for t in str(v or "").split(",") if t.strip()],
        )
        self.assertEqual(anchor, "026-0313955-0013102")


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


if __name__ == "__main__":
    unittest.main()
