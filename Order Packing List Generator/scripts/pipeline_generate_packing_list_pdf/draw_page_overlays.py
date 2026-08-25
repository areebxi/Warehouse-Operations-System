import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)
from scripts.pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)


def draw_logo_overlays_impl(
    c,
    row_series,
    *,
    is_plain_order: bool,
    has_explicit_fbpi_logo: bool,
    position_has_slash: bool,
    position_code_to_draw: Optional[Dict[str, str]],
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    logo_image_for_slot: Callable[[int], object],
    logo_design_tokens: Callable[..., List[str]],
    safe_str: Callable[..., str],
    normalize_lower: Callable[..., str],
    prepare_image: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> None:
    if is_plain_order or has_explicit_fbpi_logo:
        return

    proc = str(row_series.get("Process and Item Number", "") or "").strip()

    logo_tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
    front_chest_scale = 2.5
    front_w = aw / front_chest_scale
    front_h = ah / front_chest_scale
    front_lx = ax + aw * 0.3
    front_ly = ay + ah * 0.4

    pocket_scale = 6.0
    pocket_w = aw / pocket_scale
    pocket_h = ah / pocket_scale
    pocket_lx = ax + aw * 0.555
    pocket_ly = ay + ah * 0.675

    left_forearm_scale = 6.0
    left_forearm_w = aw / left_forearm_scale
    left_forearm_h = ah / left_forearm_scale
    left_forearm_lx = ax + aw * 0.735
    left_forearm_ly = ay + ah * 0.185

    right_forearm_scale = left_forearm_scale
    right_forearm_w = aw / right_forearm_scale
    right_forearm_h = ah / right_forearm_scale
    right_forearm_lx = ax + aw * 0.08
    right_forearm_ly = left_forearm_ly

    bottom_left_scale = 2.5
    bottom_left_w = aw / bottom_left_scale
    bottom_left_h = ah / bottom_left_scale
    bottom_left_lx = ax + aw * 0.155
    bottom_left_ly = ay + ah * 0.125

    bottom_right_scale = bottom_left_scale
    bottom_right_w = aw / bottom_right_scale
    bottom_right_h = ah / bottom_right_scale
    bottom_right_lx = ax + aw * 0.415
    bottom_right_ly = bottom_left_ly

    def _draw_overlay(
        img_path,
        lx: float,
        ly: float,
        w: float,
        h: float,
        *,
        region_key: str,
        logo_token_index: int,
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
                f"LOGO OVERLAY ({region_key}) drawn on apparel mockup | logo_token_index={logo_token_index} | "
                f"file_name={p.name!r} | full_path={abs_p}",
            )

    draw_tokens: List[str] = []
    if position_code_to_draw is not None and not position_has_slash:
        position_code = safe_str(row_series.get("Position Code", ""))
        if position_code:
            raw_draw = lookup_draw_for_position_code(position_code_to_draw, position_code)
            if raw_draw:
                draw_tokens = [t.strip() for t in str(raw_draw).split(",") if t.strip()][:5]

    geometry_keys: List[Optional[str]] = []
    for dt in draw_tokens:
        key = normalize_lower(dt)
        if not key:
            geometry_keys.append(None)
        elif key in ("front", "front center"):
            geometry_keys.append("front_chest")
        elif key == "pocket":
            geometry_keys.append("pocket")
        elif key == "front left full forearm":
            geometry_keys.append("left_front_full_forearm")
        elif key == "front right full forearm":
            geometry_keys.append("right_front_full_forearm")
        elif key == "front bottom left corner":
            geometry_keys.append("front_bottom_left")
        elif key == "front bottom right corner":
            geometry_keys.append("front_bottom_right")
        else:
            geometry_keys.append(None)

    geometry_by_key: Dict[str, Tuple[float, float, float, float]] = {
        "front_chest": (front_lx, front_ly, front_w, front_h),
        "pocket": (pocket_lx, pocket_ly, pocket_w, pocket_h),
        "left_front_full_forearm": (left_forearm_lx, left_forearm_ly, left_forearm_w, left_forearm_h),
        "right_front_full_forearm": (right_forearm_lx, right_forearm_ly, right_forearm_w, right_forearm_h),
        "front_bottom_left": (bottom_left_lx, bottom_left_ly, bottom_left_w, bottom_left_h),
        "front_bottom_right": (bottom_right_lx, bottom_right_ly, bottom_right_w, bottom_right_h),
    }

    if logo_tokens and geometry_keys:
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
            _draw_overlay(
                img_path,
                gx,
                gy,
                gw,
                gh,
                region_key=geom_key,
                logo_token_index=idx,
            )
