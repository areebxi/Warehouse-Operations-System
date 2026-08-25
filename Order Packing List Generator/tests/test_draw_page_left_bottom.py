"""Tests for left-bottom item image URL resolution (Item Image URL + Gift Message fallback)."""

from __future__ import annotations

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.draw_page_left_bottom import (
    _item_image_url_candidates,
    _url_from_gift_message,
    draw_left_bottom_item_image_impl,
)


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


def test_draw_left_bottom_uses_gift_message_when_item_url_empty():
    drawn_urls: list[str] = []

    class FakeCanvas:
        def drawImage(self, _reader, _x, _y, **kwargs):
            drawn_urls.append("drawn")

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
