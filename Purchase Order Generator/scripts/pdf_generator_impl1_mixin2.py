from __future__ import annotations
import pandas as pd
from fpdf import FPDF
from pathlib import Path
from datetime import date
from app_paths import APP_ROOT, asset_path, data_path, packs_database_path, product_database_path, tag_output_dir

class PDFMixin2:
    def _draw_product_details(self, item_data, product_data, total_items, pack_title=None):
        _colour_img_by_uid = _load_colour_image_basenames_by_uid()

        def _find_product_image(product_filename, sku_value):
            img_path, img_source, _ = _resolve_product_image_path(
                product_filename, sku_value, colour_img_by_uid=_colour_img_by_uid
            )
            if img_path:
                print(f"      Image: using {img_source} -> {img_path}")
                return img_path
            return None

        product_filename = (product_data or {}).get(COLUMN_NAMES['product_image_filename'])
        fallback_sku = item_data.get(COLUMN_NAMES['sku'])
        image_path = _find_product_image(product_filename, fallback_sku)
        if image_path:
            self._place_image(str(image_path), x=PRODUCT_IMG_X, y=PRODUCT_IMG_Y, w=PRODUCT_IMG_W, h=PRODUCT_IMG_H)

        name_y_pos = PRODUCT_IMG_Y + PRODUCT_IMG_H + 3
        self.set_xy(PRODUCT_IMG_X, name_y_pos)
        # Slightly smaller font so two lines can fit if needed
        self.set_font(self.base_font, 'B', 20)
        self.multi_cell(w=PRODUCT_IMG_W, h=8, txt=self._t(item_data.get(COLUMN_NAMES['recipient'], 'N/A')), border=0, align='C')

        self.set_xy(DETAILS_X_START, PRODUCT_IMG_Y)

        def write_detail(label, value):
            self.set_font(self.base_font, 'B', 12)
            self.set_x(DETAILS_X_START)
            self.cell(w=40, h=8, txt=self._t(label), border=0)
            self.set_font(self.base_font, '', 12)
            self.multi_cell(w=0, h=8, txt=self._t(f": {value}"), border=0)

        # Use pack_title from Packs Database.xlsx Column AI if available, otherwise fallback to Description
        title_value = pack_title if pack_title and str(pack_title).strip() else str((product_data or {}).get(COLUMN_NAMES['description'], 'N/A'))
        write_detail('Title', title_value)
        write_detail('Colour', str((product_data or {}).get(COLUMN_NAMES['colour'], 'N/A')))
        write_detail('Size', str((product_data or {}).get(COLUMN_NAMES['size'], 'N/A')))

        # Quantity styled like "Merge Order" pill if greater than 1
        quantity_value = str(item_data.get(COLUMN_NAMES['quantity'], 'N/A'))
        try:
            qty_num = int(quantity_value) if quantity_value.isdigit() else 0
            if qty_num > 1:
                self.set_x(DETAILS_X_START)
                pill_text = self._t(f"Quantity: {quantity_value}")
                self.set_font(self.base_font, 'B', 14)
                # Compute pill width with padding
                try:
                    text_w = self.get_string_width(pill_text)
                except Exception:
                    text_w = 60
                pill_w = min(120, max(60, text_w + 12))
                self.set_fill_color(255, 0, 0)
                self.set_text_color(255, 255, 255)
                self.cell(w=pill_w, h=8, txt=pill_text, fill=True, align='C')
                self.set_text_color(0, 0, 0)
                self.ln(0)
            else:
                write_detail('Quantity', quantity_value)
        except Exception:
            write_detail('Quantity', quantity_value)

        self.ln(15)

        write_detail('Our SKU', str(item_data.get(COLUMN_NAMES['sku'], 'N/A')))
        write_detail('Brand', str((product_data or {}).get(COLUMN_NAMES['brand'], 'N/A')))
        write_detail('Product Code', str((product_data or {}).get(COLUMN_NAMES['product_code'], 'N/A')))
        write_detail('Package', str((product_data or {}).get(COLUMN_NAMES['package'], 'N/A')))

        if total_items > 1:
            self.ln(5)
            self.set_x(DETAILS_X_START)
            self.set_font(self.base_font, 'B', 14)
            self.set_fill_color(255, 0, 0)
            self.set_text_color(255, 255, 255)
            self.cell(w=45, h=8, txt=self._t("Merge Order"), fill=True, align='C')
            self.set_text_color(0, 0, 0)

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

