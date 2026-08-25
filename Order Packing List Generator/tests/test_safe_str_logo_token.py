"""Regression: logo tokens must not keep pandas .0 suffix on order numbers."""

import unittest

from scripts.pipeline_fill_prime_images.helpers import _order_number_as_logo_token
from scripts.pipeline_generate_packing_list_pdf.core_helpers import (
    is_plain_order_sku_impl,
    logo_design_tokens_impl,
    safe_str_impl,
)


class SafeStrLogoTokenTests(unittest.TestCase):
    def test_safe_str_strips_integer_float(self):
        self.assertEqual(safe_str_impl(4055007854.0), "4055007854")
        self.assertEqual(safe_str_impl("4066515925.0"), "4066515925")

    def test_logo_design_tokens_use_normalized_order(self):
        tokens = logo_design_tokens_impl(4055007854.0, safe_str=safe_str_impl)
        self.assertEqual(tokens, ["4055007854"])

    def test_order_number_as_logo_token_helper(self):
        self.assertEqual(_order_number_as_logo_token(4066515925.0), "4066515925")

    def test_is_plain_order_sku(self):
        self.assertTrue(is_plain_order_sku_impl("ABC-PLAINLG-01"))
        self.assertTrue(is_plain_order_sku_impl("ABC-plain-01"))
        self.assertTrue(is_plain_order_sku_impl("PLAIN"))
        self.assertFalse(is_plain_order_sku_impl("ABC-8513LG-01"))
        self.assertFalse(is_plain_order_sku_impl(""))


if __name__ == "__main__":
    unittest.main()
