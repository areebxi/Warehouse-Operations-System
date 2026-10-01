"""Place logo images into overlay geometry slots."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)


def draw_overlay_image(
    c,
    img_path,
    lx: float,
    ly: float,
    w: float,
    h: float,
    *,
    region_key: str,
    logo_token_index: int,
    proc: str,
    prepare_image: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]],
    pdf_page_index: int,
) -> None:
    prepared_overlay = prepare_image(img_path, w, h)
    try:
        if isinstance(prepared_overlay, io.BytesIO):
            c.drawImage(
                image_reader_cls(prepared_overlay),
                lx,
                ly,
                width=w,
                height=h,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        else:
            c.drawImage(
                str(prepared_overlay),
                lx,
                ly,
                width=w,
                height=h,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
    except Exception as e:
        print(f"Logo overlay draw failed: {e!r} path={img_path}", file=sys.stderr)
        p = img_path if isinstance(img_path, Path) else Path(str(img_path))
        try:
            abs_p = str(p.resolve())
        except OSError:
            abs_p = str(p)
        _pdf_asset_log_line(
            pdf_asset_log,
            f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | "
            f"LOGO OVERLAY ({region_key}) draw FAILED | logo_token_index={logo_token_index} | "
            f"attempted file={p.name!r} | full_path={abs_p} | error={e!r}",
        )
    else:
        p = img_path if isinstance(img_path, Path) else Path(str(img_path))
        try:
            abs_p = str(p.resolve())
        except OSError:
            abs_p = str(p)
        _pdf_asset_log_line(
            pdf_asset_log,
            f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | "
            f"LOGO OVERLAY ({region_key}) drawn on apparel mockup | "
            f"logo_token_index={logo_token_index} | "
            f"file_name={p.name!r} | full_path={abs_p}",
        )


def place_logo_overlays(
    c,
    *,
    proc: str,
    logo_tokens: List[str],
    geometry_keys: List[Optional[str]],
    geometry_by_key: Dict[str, Tuple[float, float, float, float]],
    logo_image_for_slot: Callable[[int], object],
    prepare_image: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]],
    pdf_page_index: int,
) -> None:
    if not (logo_tokens and geometry_keys):
        return
    for idx, _logo_token in enumerate(logo_tokens):
        if idx >= len(geometry_keys):
            break
        geom_key = geometry_keys[idx]
        if not geom_key:
            continue
        geom = geometry_by_key.get(geom_key)
        if not geom:
            continue
        img_path = logo_image_for_slot(idx)
        if not img_path:
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | "
                f"LOGO OVERLAY ({geom_key}) not drawn | logo_token_index={idx} | "
                f"no image file resolved for this logo slot",
            )
            continue
        gx, gy, gw, gh = geom
        draw_overlay_image(
            c,
            img_path,
            gx,
            gy,
            gw,
            gh,
            region_key=geom_key,
            logo_token_index=idx,
            proc=proc,
            prepare_image=prepare_image,
            image_reader_cls=image_reader_cls,
            pdf_asset_log=pdf_asset_log,
            pdf_page_index=pdf_page_index,
        )
