"""Tests for customise logo context (front/back/pocket/sleeve side files)."""

import unittest
from pathlib import Path

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.draw_page_custom_logo_context import (
    resolve_custom_logo_context_impl,
)
from scripts.pipeline_generate_packing_list_pdf.image_lookup import (
    find_image_custom_fbpi_impl,
    find_image_custom_exact_impl,
)


def _tokens(val):
    s = str(val or "").strip()
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()][:5]


class ResolveCustomLogoContextTests(unittest.TestCase):
    def test_finds_sleeve_file_uppercase_s_segment(self):
        """Regression: 202-9359504-5073928-S-98765PER-….jpg via base-s lookup."""
        base = "202-9359504-5073928"
        sleeve_path = Path(f"{base}-S-98765PER-M-T-SPH-M-Yes.jpg")
        stem_map = {
            sleeve_path.stem: sleeve_path,
            f"{base}-98765PER-M-T-SPH-M-Yes": Path(f"{base}-98765PER-M-T-SPH-M-Yes.png"),
        }
        row = pd.Series(
            {
                "Customise": "Yes",
                "Logo/Design Image": base,
                "Item SKU": "98765PER-M-T-SPH-M-Yes",
            }
        )
        base_png = stem_map[f"{base}-98765PER-M-T-SPH-M-Yes"]
        _customised, _scoped, base_path, fbpi_slots = resolve_custom_logo_context_impl(
            row,
            {},
            is_plain_order=False,
            logo_customise_dir=None,
            logo_custom_stem_map=stem_map,
            safe_str=lambda v: str(v or "").strip(),
            logo_design_tokens=_tokens,
            find_image_custom_exact=find_image_custom_exact_impl,
            find_image_custom_logo=lambda *_a, **_k: base_png,
            find_image_custom_fbpi=find_image_custom_fbpi_impl,
        )
        self.assertEqual(base_path, base_png)
        labels = [label for _path, label in fbpi_slots]
        self.assertIn("Sleeve", labels)
        sleeve_entry = next(p for p, lbl in fbpi_slots if lbl == "Sleeve")
        self.assertEqual(sleeve_entry, sleeve_path)

    def test_finds_all_four_side_suffixes(self):
        base = "order-1"
        stem_map = {
            f"{base}-f-extra": Path(f"{base}-f-extra.jpg"),
            f"{base}-b-extra": Path(f"{base}-b-extra.jpg"),
            f"{base}-p-extra": Path(f"{base}-p-extra.jpg"),
            f"{base}-S-extra": Path(f"{base}-S-extra.jpg"),
            base: Path(f"{base}.png"),
        }
        row = pd.Series({"Customise": "Yes", "Logo/Design Image": base})
        _customised, _scoped, _base_path, fbpi_slots = resolve_custom_logo_context_impl(
            row,
            {},
            is_plain_order=False,
            logo_customise_dir=None,
            logo_custom_stem_map=stem_map,
            safe_str=lambda v: str(v or "").strip(),
            logo_design_tokens=_tokens,
            find_image_custom_exact=find_image_custom_exact_impl,
            find_image_custom_logo=lambda *_a, **_k: stem_map[base],
            find_image_custom_fbpi=find_image_custom_fbpi_impl,
        )
        self.assertEqual(
            [label for _path, label in fbpi_slots],
            ["Front", "Back", "Pocket", "Sleeve"],
        )

    def test_scoped_merge_finds_pocket_with_item_sku(self):
        base = "026-0313955-0013102-1"
        item_sku = "161890LG-M-T-FUC-L-YES"
        pocket_path = Path(f"{base}-p-{item_sku}.png")
        stem_map = {pocket_path.stem: pocket_path, base: Path(f"{base}.png")}
        row = pd.Series(
            {
                "Customise": "Yes",
                "Logo/Design Image": base,
                "Item SKU": item_sku,
                "Order Number (Base)": "026-0313955-0013102",
            }
        )
        _customised, scoped, _base_path, fbpi_slots = resolve_custom_logo_context_impl(
            row,
            {"026-0313955-0013102": 2},
            is_plain_order=False,
            logo_customise_dir=None,
            logo_custom_stem_map=stem_map,
            safe_str=lambda v: str(v or "").strip(),
            logo_design_tokens=_tokens,
            find_image_custom_exact=find_image_custom_exact_impl,
            find_image_custom_logo=lambda *_a, **_k: None,
            find_image_custom_fbpi=find_image_custom_fbpi_impl,
        )
        self.assertTrue(scoped)
        self.assertEqual(fbpi_slots, [(pocket_path, "Pocket")])


if __name__ == "__main__":
    unittest.main()
