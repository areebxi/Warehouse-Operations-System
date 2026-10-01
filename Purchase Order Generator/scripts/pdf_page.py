"""PDF packing-slip page class (single + pack)."""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from pdf_constants import (
    BRAND_IMAGE_FOLDER,
    BRAND_LOGO_W,
    BRAND_LOGO_X,
    COLUMN_NAMES,
    MARGIN,
)
from pdf_page_details import ProductDetailsMixin
from pdf_page_pack import PackSlipMixin


class PDF(ProductDetailsMixin, PackSlipMixin, FPDF):
    """Generates one packing slip page per item."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force built-in Helvetica (ASCII) to avoid any machine-specific font paths.
        self.base_font = 'Helvetica'
        self._supports_unicode = False
        self.set_font(self.base_font, '', 12)

    def _t(self, value: object) -> str:
        """Return text safe for current font. Converts to latin-1 if unicode not supported."""
        s = str(value) if value is not None else ''
        if self._supports_unicode:
            return s
        # Fallback: replace common symbols and strip unsupported chars
        replacements = {
            '™': 'TM', '®': 'R', '©': 'C', '–': '-', '—': '-', '’': "'", '‘': "'", '“': '"', '”': '"', '•': '-',
        }
        for k, v in replacements.items():
            s = s.replace(k, v)
        try:
            return s.encode('latin-1', 'ignore').decode('latin-1')
        except Exception:
            return s

    def _place_image(self, image_path, x, y, w=0, h=0):
        """Helper method to check for and place an image, handling errors."""
        if not isinstance(image_path, str) or not image_path.strip():
            return

        path_obj = Path(image_path)
        if not path_obj.exists():
            print(f"      Warning: Image file not found at: {path_obj}")
            return

        # Internal helper to call fpdf.image safely even if Pillow is unavailable in runtime (e.g., EXE)
        def _safe_fpfd_image(path_str, x_val, y_val, w_val=0, h_val=0):
            try:
                self.image(path_str, x=x_val, y=y_val, w=w_val, h=h_val)
            except Exception as img_err:
                print(f"      Warning: Could not place image '{path_obj}': {img_err}. Skipping image.")

        # If both width and height are specified, maintain aspect ratio
        if w > 0 and h > 0:
            try:
                from PIL import Image
                with Image.open(path_obj) as img:
                    img_ratio = img.size[0] / img.size[1]  # width/height
                    box_ratio = w / h
                    
                    if img_ratio > box_ratio:
                        # Image is wider than box, fit to width
                        new_w = w
                        new_h = w / img_ratio
                    else:
                        # Image is taller than box, fit to height
                        new_h = h
                        new_w = h * img_ratio
                    
                    # Center the image in the box
                    offset_x = (w - new_w) / 2
                    offset_y = (h - new_h) / 2
                    
                    _safe_fpfd_image(str(path_obj), x + offset_x, y + offset_y, new_w, new_h)
            except ImportError:
                # Fallback to original behavior if PIL not available
                _safe_fpfd_image(str(path_obj), x, y, w, h)
            except Exception as e:
                print(f"      Warning: Error processing image {path_obj}: {e}")
                # Fallback to original behavior
                _safe_fpfd_image(str(path_obj), x, y, w, h)
        else:
            _safe_fpfd_image(str(path_obj), x, y, w, h)

    def _draw_header(self, item_data, product_data, item_count, total_items):
        # Use Process No from CSV if available, otherwise fallback to Tag ID
        process_value = item_data.get('Process No', '') or item_data.get(COLUMN_NAMES['process'], '')
        self.set_font(self.base_font, 'B', 24)
        self.cell(w=100, h=10, txt=self._t(f"Process: {process_value}"))

        self.set_font(self.base_font, 'B', 12)
        item_counter_text = f"Item {item_count} of {total_items}" if total_items > 1 else ""
        self.cell(w=90, h=10, txt=self._t(item_counter_text), align='C')

        brand_filename = product_data.get(COLUMN_NAMES['brand_image_filename']) if isinstance(product_data, dict) else None
        logo_path = BRAND_IMAGE_FOLDER / str(brand_filename) if brand_filename else None
        if logo_path:
            self._place_image(str(logo_path), x=BRAND_LOGO_X, y=MARGIN, w=BRAND_LOGO_W)

        self.ln(10)
        self.set_font(self.base_font, 'B', 24)
        self.set_x(90)
        self.cell(w=110, h=12, txt=self._t(item_data.get(COLUMN_NAMES['order_id'], 'N/A')), align='C')
        self.ln(15)
