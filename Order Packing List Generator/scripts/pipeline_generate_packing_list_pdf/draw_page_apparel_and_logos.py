import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from scripts.pipeline_generate_packing_list_pdf.back_print_hint import (
    next_logo_slot_index,
    slot_is_back_print,
)

_LOGO_FIELDS = (
    "Logo/Design Image (1st)",
    "Logo/Design Image (2nd)",
    "Logo/Design Image (3rd)",
    "Logo/Design Image (4th)",
    "Logo/Design Image (5th)",
)

_SLOT_LABELS = (
    "logo slot 1 (1st)",
    "logo slot 2 (2nd)",
    "logo slot 3 (3rd)",
    "logo slot 4 (4th)",
    "logo slot 5 (5th)",
)


def _pdf_asset_log_line(log: Optional[Callable[[str], None]], line: str) -> None:
    if not log:
        return
    try:
        log(line)
    except Exception:
        pass


def _draw_prepared_image(
    c,
    prepared: object,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    image_reader_cls,
) -> None:
    if isinstance(prepared, io.BytesIO):
        c.drawImage(
            image_reader_cls(prepared),
            lx,
            ly,
            width=lw,
            height=lh,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
    else:
        c.drawImage(
            str(prepared),
            lx,
            ly,
            width=lw,
            height=lh,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )


def _draw_red_margin(c, lx: float, ly: float, lw: float, lh: float) -> None:
    line_w = max(1.5, min(lw, lh) * 0.02)
    c.setStrokeColorRGB(1, 0, 0)
    c.setLineWidth(line_w)
    c.rect(lx, ly, lw, lh, fill=0, stroke=1)


def _draw_back_print_reference(
    c,
    ref_path: Path,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    *,
    prepare_image: Callable[..., object],
    image_reader_cls,
) -> None:
    prepared_ref = prepare_image(ref_path, lw, lh)
    _draw_prepared_image(c, prepared_ref, lx, ly, lw, lh, image_reader_cls)
    _draw_red_margin(c, lx, ly, lw, lh)


def _draw_logo_cell_image(
    c,
    img_path: Path,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    *,
    slot_index: int,
    slot_label: str,
    proc: str,
    row_series,
    fbpi_slots: List[Tuple[Path, str]],
    position_code_to_draw: Optional[Dict[str, str]],
    default_position_code: str,
    safe_str: Callable[..., str],
    position_tokens: Callable[..., List[str]],
    logo_design_tokens: Callable[..., List[str]],
    back_print_image_path: Optional[Path],
    prepare_image: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]],
    pdf_page_index: int,
    use_split_fallback: bool,
    next_col_rect: Optional[Tuple[float, float, float, float]],
) -> None:
    show_back_hint = slot_is_back_print(
        slot_index,
        img_path,
        fbpi_slots=fbpi_slots,
        row_series=row_series,
        position_code_to_draw=position_code_to_draw,
        default_position_code=default_position_code,
        safe_str=safe_str,
        position_tokens=position_tokens,
        logo_design_tokens=logo_design_tokens,
    )

    if show_back_hint:
        ref_path = back_print_image_path
        has_ref_file = ref_path is not None and ref_path.is_file()

        if use_split_fallback:
            half_w = lw / 2
            prepared_logo = prepare_image(img_path, half_w, lh)
            _draw_prepared_image(c, prepared_logo, lx, ly, half_w, lh, image_reader_cls)
            _draw_red_margin(c, lx, ly, half_w, lh)
            if has_ref_file:
                _draw_back_print_reference(
                    c, ref_path, lx + half_w, ly, half_w, lh,
                    prepare_image=prepare_image, image_reader_cls=image_reader_cls,
                )
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                    f"back-print hint drawn (split cell fallback) | logo={img_path.name!r} | "
                    f"reference={ref_path.name!r}",
                )
            else:
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                    f"back-print hint partial (split cell, logo only) | "
                    f"reference image missing | expected={ref_path!r}",
                )
            return

        prepared_logo = prepare_image(img_path, lw, lh)
        _draw_prepared_image(c, prepared_logo, lx, ly, lw, lh, image_reader_cls)
        _draw_red_margin(c, lx, ly, lw, lh)

        if next_col_rect is not None and has_ref_file:
            nx, ny, nw, nh = next_col_rect
            _draw_back_print_reference(
                c, ref_path, nx, ny, nw, nh,
                prepare_image=prepare_image, image_reader_cls=image_reader_cls,
            )
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                f"back-print hint drawn (next column) | logo={img_path.name!r} | "
                f"reference={ref_path.name!r}",
            )
        else:
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                f"back-print hint partial (logo only) | reference image missing | "
                f"expected={ref_path!r}",
            )
        return

    prepared = prepare_image(img_path, lw, lh)
    _draw_prepared_image(c, prepared, lx, ly, lw, lh, image_reader_cls)


def _compute_back_print_layout(
    row_series,
    order_number_counts: dict,
    *,
    logo_image_for_slot: Callable[[int], Optional[Path]],
    get_field_value: Callable[..., str],
    fbpi_slots: List[Tuple[Path, str]],
    logo_design_tokens: Callable[..., List[str]],
    position_code_to_draw: Optional[Dict[str, str]],
    default_position_code: str,
    safe_str: Callable[..., str],
    position_tokens: Callable[..., List[str]],
) -> Tuple[Set[int], Set[int]]:
    """Return (slots_using_split_fallback, slots_reserved_for_back_reference_only)."""
    split_fallback: Set[int] = set()
    ref_only_slots: Set[int] = set()

    def _slot_has_own_logo(slot_index: int) -> bool:
        if logo_image_for_slot(slot_index) is not None:
            return True
        return bool(get_field_value(row_series, _LOGO_FIELDS[slot_index], order_number_counts))

    for slot_index in range(5):
        img_path = logo_image_for_slot(slot_index)
        if not slot_is_back_print(
            slot_index,
            img_path,
            fbpi_slots=fbpi_slots,
            row_series=row_series,
            position_code_to_draw=position_code_to_draw,
            default_position_code=default_position_code,
            safe_str=safe_str,
            position_tokens=position_tokens,
            logo_design_tokens=logo_design_tokens,
        ):
            continue

        next_slot = next_logo_slot_index(slot_index)
        if next_slot is not None and not _slot_has_own_logo(next_slot):
            ref_only_slots.add(next_slot)
        else:
            split_fallback.add(slot_index)

    return split_fallback, ref_only_slots


def draw_apparel_square_impl(
    c,
    row_series,
    order_number_counts: dict,
    *,
    is_plain_order: bool,
    image_area_x_pt: float,
    s1_y_pt: float,
    col_w_pt: float,
    square_s_pt: float,
    font_size_banner: float,
    black,
    red,
    rect_at: Callable[..., tuple],
    get_field_value: Callable[..., str],
    safe_str: Callable[..., str],
    find_image: Callable[..., Optional[Path]],
    apparel_image_dir,
    apparel_stem_map,
    prepare_image: Callable[..., object],
    draw_text_in_box: Callable[..., None],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> tuple[float, float, float, float, bool]:
    had_missing_apparel = False
    ax, ay, aw, ah = rect_at(image_area_x_pt, s1_y_pt, col_w_pt, square_s_pt)
    apparel_text = get_field_value(row_series, "Apparel Image", order_number_counts)
    has_apparel_lookup = apparel_image_dir is not None or apparel_stem_map is not None
    apparel_img_path: Optional[Path] = None
    if has_apparel_lookup:
        for name in (apparel_text, safe_str(row_series.get("Picture Name", ""))):
            if not name:
                continue
            candidate = find_image(apparel_image_dir, name, apparel_stem_map, recursive=False)
            if candidate is not None:
                apparel_img_path = candidate
                break
    if apparel_img_path:
        prepared = prepare_image(apparel_img_path, aw, ah)
        proc = safe_str(row_series.get("Process and Item Number", ""))
        try:
            _draw_prepared_image(c, prepared, ax, ay, aw, ah, image_reader_cls)
        except Exception as exc:
            had_missing_apparel = True
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | APPAREL draw FAILED | "
                f"attempted file={apparel_img_path.name!r} | path={apparel_img_path} | error={exc!r}",
            )
            draw_text_in_box(c, ax, ay, aw, ah, apparel_text, False, black, "center")
        else:
            try:
                abs_path = str(apparel_img_path.resolve())
            except OSError:
                abs_path = str(apparel_img_path)
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | APPAREL drawn on PDF | "
                f"file_name={apparel_img_path.name!r} | full_path={abs_path}",
            )
    elif apparel_text:
        had_missing_apparel = True
        proc = safe_str(row_series.get("Process and Item Number", ""))
        _pdf_asset_log_line(
            pdf_asset_log,
            f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | APPAREL not drawn | "
            f"no image file resolved for tokens Apparel Image={apparel_text!r} "
            f"Picture Name={safe_str(row_series.get('Picture Name', ''))!r}",
        )
        draw_text_in_box(c, ax, ay, aw, ah, "A", True, red, "center", font_size=font_size_banner + 8)
    else:
        draw_text_in_box(c, ax, ay, aw, ah, apparel_text, False, black, "center")
    return ax, ay, aw, ah, had_missing_apparel


def draw_logo_square_rows_impl(
    c,
    row_series,
    order_number_counts: dict,
    *,
    is_plain_order: bool,
    image_area_x_pt: float,
    col_w_pt: float,
    s1_y_pt: float,
    s2_y_pt: float,
    square_s_pt: float,
    s2_square_h_pt: float,
    font_size_banner: float,
    black,
    red,
    rect_at: Callable[..., tuple],
    get_field_value: Callable[..., str],
    logo_image_for_slot: Callable[[int], Optional[Path]],
    prepare_image: Callable[..., object],
    draw_text_in_box: Callable[..., None],
    image_reader_cls,
    fbpi_slots: Optional[List[Tuple[Path, str]]] = None,
    position_code_to_draw: Optional[Dict[str, str]] = None,
    default_position_code: str = "X",
    position_tokens: Optional[Callable[..., List[str]]] = None,
    safe_str: Optional[Callable[..., str]] = None,
    back_print_image_path: Optional[Path] = None,
    logo_design_tokens: Optional[Callable[..., List[str]]] = None,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> bool:
    had_missing_logo = False
    proc = str(row_series.get("Process and Item Number", "") or "").strip()
    fbpi_slots = fbpi_slots or []
    _safe_str = safe_str or (lambda v: str(v or "").strip())
    _position_tokens = position_tokens or (lambda _v: [])
    _logo_design_tokens = logo_design_tokens or (lambda _v: [])

    slot_grid = [
        (1, 0, s1_y_pt, square_s_pt),
        (2, 1, s1_y_pt, square_s_pt),
        (0, 2, s2_y_pt, s2_square_h_pt),
        (1, 3, s2_y_pt, s2_square_h_pt),
        (2, 4, s2_y_pt, s2_square_h_pt),
    ]

    split_fallback_slots: Set[int] = set()
    back_ref_only_slots: Set[int] = set()
    if not is_plain_order:
        split_fallback_slots, back_ref_only_slots = _compute_back_print_layout(
            row_series,
            order_number_counts,
            logo_image_for_slot=logo_image_for_slot,
            get_field_value=get_field_value,
            fbpi_slots=fbpi_slots,
            logo_design_tokens=_logo_design_tokens,
            position_code_to_draw=position_code_to_draw,
            default_position_code=default_position_code,
            safe_str=_safe_str,
            position_tokens=_position_tokens,
        )

    def _cell_rect(col: int, y_pt: float, h_pt: float) -> Tuple[float, float, float, float]:
        return rect_at(image_area_x_pt + col * col_w_pt, y_pt, col_w_pt, h_pt)

    def _draw_slot(col: int, idx: int, y_pt: float, h_pt: float) -> None:
        nonlocal had_missing_logo
        lx, ly, lw, lh = _cell_rect(col, y_pt, h_pt)
        slot_label = _SLOT_LABELS[idx]
        logo_field = _LOGO_FIELDS[idx]

        if is_plain_order:
            if idx == 0 and y_pt == s1_y_pt:
                draw_text_in_box(c, lx, ly, lw, lh, "Plain Order", True, red, "center", font_size=font_size_banner)
            else:
                draw_text_in_box(c, lx, ly, lw, lh, "", False, black, "center")
            return

        if idx in back_ref_only_slots:
            return

        logo_val = get_field_value(row_series, logo_field, order_number_counts)
        img_path = logo_image_for_slot(idx)
        if img_path:
            next_col_rect: Optional[Tuple[float, float, float, float]] = None
            if idx not in split_fallback_slots:
                next_slot = next_logo_slot_index(idx)
                if next_slot is not None and next_slot in back_ref_only_slots:
                    ncol, _nidx, ny_pt, nh_pt = slot_grid[next_slot]
                    next_col_rect = _cell_rect(ncol, ny_pt, nh_pt)

            try:
                _draw_logo_cell_image(
                    c,
                    img_path,
                    lx,
                    ly,
                    lw,
                    lh,
                    slot_index=idx,
                    slot_label=slot_label,
                    proc=proc,
                    row_series=row_series,
                    fbpi_slots=fbpi_slots,
                    position_code_to_draw=position_code_to_draw,
                    default_position_code=default_position_code,
                    safe_str=_safe_str,
                    position_tokens=_position_tokens,
                    logo_design_tokens=_logo_design_tokens,
                    back_print_image_path=back_print_image_path,
                    prepare_image=prepare_image,
                    image_reader_cls=image_reader_cls,
                    pdf_asset_log=pdf_asset_log,
                    pdf_page_index=pdf_page_index,
                    use_split_fallback=idx in split_fallback_slots,
                    next_col_rect=next_col_rect,
                )
            except Exception as e:
                had_missing_logo = True
                print(f"Logo draw failed: {e!r} path={img_path}", file=sys.stderr)
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} draw FAILED | "
                    f"attempted file={img_path.name!r} | path={img_path} | error={e!r}",
                )
                draw_text_in_box(c, lx, ly, lw, lh, "L", True, red, "center", font_size=font_size_banner + 8)
            else:
                try:
                    abs_p = str(img_path.resolve())
                except OSError:
                    abs_p = str(img_path)
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label.upper()} drawn on PDF | "
                    f"file_name={img_path.name!r} | full_path={abs_p}",
                )
        elif logo_val:
            had_missing_logo = True
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} not drawn | "
                f"no file for field value={logo_val!r}",
            )
            draw_text_in_box(c, lx, ly, lw, lh, "L", True, red, "center", font_size=font_size_banner + 8)
        else:
            draw_text_in_box(c, lx, ly, lw, lh, "", False, black, "center")

    for col, idx, y_pt, h_pt in slot_grid:
        _draw_slot(col, idx, y_pt, h_pt)

    return had_missing_logo
