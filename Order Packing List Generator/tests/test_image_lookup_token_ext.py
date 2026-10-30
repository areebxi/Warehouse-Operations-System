"""Apparel tokens with .jpg (Plain Product_Image_URL) must resolve to stem files."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.pipeline_generate_packing_list_pdf.image_lookup_find import find_image_impl
from scripts.pipeline_generate_packing_list_pdf.image_lookup_stem import (
    normalize_image_lookup_token,
    probe_exact_image_impl,
)


def test_normalize_strips_known_image_ext() -> None:
    assert normalize_image_lookup_token("prod_1.jpg") == "prod_1"
    assert normalize_image_lookup_token("prod_1.PNG") == "prod_1"
    assert normalize_image_lookup_token("prod_1") == "prod_1"
    assert normalize_image_lookup_token("a.b.custom") == "a.b.custom"


def test_probe_and_find_accept_filename_with_ext() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "prod_15009_64000_184585.jpg"
        target.write_bytes(b"x")
        assert probe_exact_image_impl(root, "prod_15009_64000_184585.jpg") == target
        assert find_image_impl(root, "prod_15009_64000_184585.jpg", None) == target
        stem_map = {"prod_15009_64000_184585": target}
        assert find_image_impl(root, "prod_15009_64000_184585.jpg", stem_map) == target
