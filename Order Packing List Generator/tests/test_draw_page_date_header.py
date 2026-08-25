import unittest
from unittest.mock import MagicMock

from scripts.pipeline_generate_packing_list_pdf.draw_page_date_header import (
    draw_page_date_header_impl,
    format_dispatch_date_header,
)
from scripts.pipeline_generate_packing_list_pdf import pdf_page_layout as L


class DrawPageDateHeaderTests(unittest.TestCase):
    def test_format_dispatch_date_header_known_thursday(self):
        date_label, day_name = format_dispatch_date_header("11-06-2026")
        self.assertEqual(date_label, "11-06-2026")
        self.assertEqual(day_name, "Thursday")

    def test_format_dispatch_date_header_accepts_slashes(self):
        date_label, day_name = format_dispatch_date_header("11/06/2026")
        self.assertEqual(date_label, "11-06-2026")
        self.assertEqual(day_name, "Thursday")

    def test_format_dispatch_date_header_invalid_raises(self):
        with self.assertRaises(ValueError):
            format_dispatch_date_header("not-a-date")

    def test_draw_page_date_header_impl(self):
        canvas = MagicMock()
        draw_page_date_header_impl(canvas, "11-06-2026", "Thursday")
        canvas.setFont.assert_called_once_with(L.FONT_NAME, L.DATE_HEADER_FONT_SIZE)
        canvas.setFillColorRGB.assert_called_once_with(*L.BLACK)
        canvas.drawString.assert_called_once_with(
            L.MARGIN_LR,
            L.PAGE_HEIGHT - L.DATE_HEADER_TOP_OFFSET,
            "11-06-2026  Thursday",
        )


if __name__ == "__main__":
    unittest.main()
