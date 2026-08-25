"""Text drawing helpers for packing list PDFs (wrapped lines, recipient styling)."""

from __future__ import annotations

from typing import Dict, List, Tuple

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from scripts.pipeline_generate_packing_list_pdf.core_helpers import truncate_impl

from . import pdf_page_layout as L

_FONT_METRICS_CACHE: Dict[Tuple[str, float], Tuple[float, float]] = {}


def _get_font_ascent_descent(font: str, font_size: float) -> Tuple[float, float]:
    """Return (ascent_pt, descent_pt) for vertical centering; cached per (font, font_size)."""
    key = (font, font_size)
    if key not in _FONT_METRICS_CACHE:
        try:
            face = pdfmetrics.getFont(font).face
            ascent_pt = (face.ascent / 1000.0) * font_size
            descent_pt = (face.descent / 1000.0) * font_size
        except Exception:
            ascent_pt = font_size * 0.72
            descent_pt = -font_size * 0.28
        _FONT_METRICS_CACHE[key] = (ascent_pt, descent_pt)
    return _FONT_METRICS_CACHE[key]


def draw_text_in_box_impl(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    bold: bool,
    color_rgb,
    align: str = "left",
    font_size: float = L.FONT_SIZE,
    vertical_nudge: float = 0,
    wrap: bool = False,
) -> None:
    if not text:
        return
    font = L.FONT_BOLD if bold else L.FONT_NAME
    c.setFillColorRGB(*color_rgb)
    c.setFont(font, font_size)
    if not wrap:
        # Single-line text with horizontal alignment and vertical centering
        text = truncate_impl(text, max(1, int(w / (font_size * 0.5)) - 1))
        tw = c.stringWidth(text, font, font_size)
        if align == "center":
            x = x + (w - tw) / 2
        elif align == "right":
            x = x + w - tw
        # Vertical center: use font face metrics (in 1000ths) scaled by font_size
        ascent_pt, descent_pt = _get_font_ascent_descent(font, font_size)
        # Text vertical center from baseline: (ascent_pt + descent_pt) / 2
        text_center_from_baseline = (ascent_pt + descent_pt) / 2.0
        baseline = y + h / 2.0 - text_center_from_baseline + vertical_nudge
        c.drawString(x, baseline, text)
        return

    # Multi-line wrapping: break text into lines that fit width w
    words = text.split()
    if not words:
        return
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if c.stringWidth(candidate, font, font_size) <= w or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if not lines:
        return

    line_height = font_size * 1.2
    total_height = line_height * len(lines)
    # Vertically center the block of wrapped lines inside the box
    start_y = y + (h + total_height) / 2.0 - line_height + vertical_nudge

    for i, line in enumerate(lines):
        lx = x
        tw = c.stringWidth(line, font, font_size)
        if align == "center":
            lx = x + (w - tw) / 2
        elif align == "right":
            lx = x + w - tw
        ly = start_y - i * line_height
        c.drawString(lx, ly, line)


def draw_text_in_padded_box_impl(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    bold: bool,
    color_rgb,
    align: str = "left",
    font_size: float = L.FONT_SIZE,
    vertical_nudge: float = 0,
    wrap: bool = False,
    pad_x_pt: float = L.BOX_PAD_X_PT,
    pad_y_pt: float = L.BOX_PAD_Y_PT,
) -> None:
    """Draw text inside a box with uniform inner padding."""
    if not text:
        return
    pad_x = L.pt_w(pad_x_pt)
    pad_y = L.pt_h(pad_y_pt)
    x_padded = x + pad_x
    y_padded = y + pad_y
    w_padded = max(0.0, w - 2 * pad_x)
    h_padded = max(0.0, h - 2 * pad_y)
    draw_text_in_box_impl(
        c,
        x_padded,
        y_padded,
        w_padded,
        h_padded,
        text,
        bold,
        color_rgb,
        align,
        font_size,
        vertical_nudge,
        wrap,
    )


def draw_recipient_name_in_box_impl(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    vertical_nudge: float = 0,
) -> None:
    if not text:
        return

    font = L.FONT_BOLD
    base_size = L.FONT_SIZE_BANNER
    big_size = base_size * 1.75

    c.setFillColorRGB(*L.WHITE)

    # Build wrapped lines at base font size, similar to draw_text_in_box_impl (wrap=True)
    words = text.split()
    if not words:
        return

    lines: List[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if c.stringWidth(candidate, font, base_size) <= w or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if not lines:
        return

    line_height = base_size * 1.2
    total_height = line_height * len(lines)
    start_y = y + (h + total_height) / 2.0 - line_height + vertical_nudge

    for i, line in enumerate(lines):
        baseline = start_y - i * line_height
        if i == 0:
            # First line: emphasize first three characters and first three characters after the first space,
            # both at 2× size, with the rest at base size.
            first_prefix_end = min(3, len(line))

            # Find the first space after the initial big segment.
            space_idx = line.find(" ", first_prefix_end)

            segments: List[Tuple[str, float]] = []

            if first_prefix_end > 0:
                # Segment 1: first up-to-3 characters (big).
                segments.append((line[0:first_prefix_end], big_size))

            if space_idx != -1 and space_idx + 1 < len(line):
                # We have at least a second word.
                second_prefix_start = space_idx + 1
                second_prefix_end = min(second_prefix_start + 3, len(line))

                # Segment 2: text between the first big segment and the start of the second word (including space).
                middle = line[first_prefix_end:second_prefix_start]
                if middle:
                    segments.append((middle, base_size))

                # Segment 3: first up-to-3 characters of the second word (big).
                second_prefix = line[second_prefix_start:second_prefix_end]
                if second_prefix:
                    segments.append((second_prefix, big_size))

                # Segment 4: remainder of the line after the second big segment (base).
                tail = line[second_prefix_end:]
                if tail:
                    segments.append((tail, base_size))
            else:
                # Fallback: only first up-to-3 characters big, rest base size (existing behavior).
                suffix = line[first_prefix_end:]
                if suffix:
                    segments.append((suffix, base_size))

            # Compute total width of all segments.
            total_width = 0.0
            for text_segment, size in segments:
                c.setFont(font, size)
                total_width += c.stringWidth(text_segment, font, size)

            # Left-align the first (styled) line within the box.
            lx = x

            # Draw segments sequentially along the baseline.
            cx = lx
            for text_segment, size in segments:
                if not text_segment:
                    continue
                c.setFont(font, size)
                c.drawString(cx, baseline, text_segment)
                cx += c.stringWidth(text_segment, font, size)
        else:
            c.setFont(font, base_size)
            tw = c.stringWidth(line, font, base_size)
            # Left-align subsequent lines within the box.
            lx = x
            c.drawString(lx, baseline, line)
