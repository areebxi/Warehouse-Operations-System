"""Tests for left-bottom item image URL resolution (Item Image URL + Gift Message fallback)."""

from __future__ import annotations

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.draw_page_left_bottom import (
    _item_image_url_candidates,
    _notes_from_buyer,
    _url_from_gift_message,
    _wrap_preserving_newlines,
    draw_left_bottom_item_image_impl,
)
from scripts.pipeline_generate_packing_list_pdf import pdf_page_layout as L


def _safe_str(value) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value).strip()


def test_url_from_gift_message_bare_url():
    assert _url_from_gift_message("https://i.ebayimg.com/foo.jpg") == "https://i.ebayimg.com/foo.jpg"


def test_url_from_gift_message_embedded_in_text():
    text = "Love Scotland https://example.com/custom.png and more"
    assert _url_from_gift_message(text) == "https://example.com/custom.png"


def test_item_image_url_candidates_prefers_item_column():
    row = pd.Series(
        {
            "Item Image URL": "https://example.com/item.jpg",
            "Gift Message": "https://example.com/gift.jpg",
        }
    )
    assert _item_image_url_candidates(row, _safe_str) == [
        ("https://example.com/item.jpg", "Item Image URL"),
        ("https://example.com/gift.jpg", "Gift Message"),
    ]


def test_item_image_url_candidates_falls_back_to_gift_message():
    row = pd.Series(
        {
            "Item Image URL": "",
            "Gift Message": "https://example.com/gift.jpg",
        }
    )
    assert _item_image_url_candidates(row, _safe_str) == [
        ("https://example.com/gift.jpg", "Gift Message"),
    ]


def test_notes_from_buyer_prefers_internal_name():
    row = pd.Series(
        {
            "Notes From Buyer": "internal",
            "Notes - From Buyer": "dashed",
        }
    )
    assert _notes_from_buyer(row, _safe_str) == "internal"


def test_notes_from_buyer_falls_back_to_dashed():
    row = pd.Series({"Notes - From Buyer": "dashed only"})
    assert _notes_from_buyer(row, _safe_str) == "dashed only"


def test_wrap_preserving_newlines_keeps_hard_breaks():
    def sw(text: str, _font: str, _size: float) -> float:
        return float(len(text))

    lines = _wrap_preserving_newlines("Line A\nLine B", 100.0, "Helvetica-Bold", 11.0, sw)
    assert lines == ["Line A", "Line B"]


def test_wrap_preserving_newlines_wraps_long_line():
    def sw(text: str, _font: str, _size: float) -> float:
        return float(len(text))

    lines = _wrap_preserving_newlines("aa bb cc", 5.0, "Helvetica-Bold", 11.0, sw)
    assert lines == ["aa bb", "cc"]


def test_draw_left_bottom_uses_gift_message_when_item_url_empty():
    drawn_urls: list[str] = []

    class FakeCanvas:
        def drawImage(self, _reader, _x, _y, **kwargs):
            drawn_urls.append("drawn")

        def stringWidth(self, text, _font, _size):
            return float(len(text))

        def setFillColorRGB(self, *_args):
            return None

        def setFont(self, *_args):
            return None

        def rect(self, *_args, **_kwargs):
            return None

        def drawString(self, *_args):
            return None

    def prepare_image_from_url(url, _w, _h):
        if url == "https://example.com/gift.jpg":
            return b"fake-image"
        return None

    row = pd.Series({"Item Image URL": "", "Gift Message": "https://example.com/gift.jpg"})

    draw_left_bottom_item_image_impl(
        FakeCanvas(),
        row,
        is_plain_order=False,
        content_h_pt=100.0,
        s2_y_pt=40.0,
        left_w_pt=50.0,
        rect_at=lambda *_args: (0, 0, 10, 10),
        safe_str=_safe_str,
        prepare_image_from_url=prepare_image_from_url,
        image_reader_cls=lambda data: data,
    )
    assert drawn_urls == ["drawn"]


def test_draw_left_bottom_note_shrinks_image_height():
    image_heights: list[float] = []
    drawn_strings: list[str] = []

    class FakeCanvas:
        def drawImage(self, _reader, _x, _y, **kwargs):
            image_heights.append(float(kwargs.get("height") or 0))

        def stringWidth(self, text, _font, _size):
            return float(len(text)) * 4.0

        def setFillColorRGB(self, *_args):
            return None

        def setFont(self, *_args):
            return None

        def rect(self, *_args, **_kwargs):
            return None

        def drawString(self, _x, _y, text):
            drawn_strings.append(text)

    row = pd.Series(
        {
            "Item Image URL": "https://example.com/item.jpg",
            "Notes From Buyer": "Please post ASAP",
        }
    )

    draw_left_bottom_item_image_impl(
        FakeCanvas(),
        row,
        is_plain_order=False,
        content_h_pt=100.0,
        s2_y_pt=40.0,
        left_w_pt=50.0,
        rect_at=lambda *_args: (0, 0, 200, 100),
        safe_str=_safe_str,
        prepare_image_from_url=lambda _url, _w, _h: b"img",
        image_reader_cls=lambda data: data,
    )
    assert drawn_strings
    assert drawn_strings[0].startswith(L.NOTE_FROM_BUYER_PREFIX)
    assert image_heights and image_heights[0] < 100.0
