"""ponytail: demo image self-check — fails if placeholders or fallback lookup break."""

from __future__ import annotations

import sys
from pathlib import Path

_WAREHOUSE = Path(__file__).resolve().parent.parent
_PACKING = _WAREHOUSE / "Order Packing List Generator"
for p in (_WAREHOUSE, _PACKING):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from shared.demo_images import demo_image_lookup, effective_image_dirs, ensure_demo_images  # noqa: E402
from shared import paths as wh  # noqa: E402


def main() -> None:
    ensure_demo_images()
    root = wh.demo_images_root()
    for folder in (
        wh.demo_apparel_dir(),
        wh.demo_normal_design_dir(),
        wh.demo_custom_single_dir(),
        wh.demo_custom_double_dir(),
    ):
        demo = folder / "demo.png"
        assert demo.is_file(), f"missing demo placeholder: {demo}"

    apparel, normal, single, double = effective_image_dirs(True, None, None, None, None)
    assert apparel == wh.demo_apparel_dir()
    assert normal == wh.demo_normal_design_dir()

    from scripts.pipeline_generate_packing_list_pdf.image_lookup import (
        find_image_impl,
        find_image_normal_logo_impl,
    )

    with demo_image_lookup(True):
        assert find_image_impl(apparel, "any-apparel-stem", None) is not None
        assert find_image_normal_logo_impl(normal, "8513LG", None) is not None

    print(f"demo images ok ({root})")


if __name__ == "__main__":
    main()
