"""Single-item product details drawing for packing slips."""
from __future__ import annotations

from pdf_btc_images import _load_colour_image_basenames_by_uid, _resolve_product_image_path
from pdf_constants import (
    COLUMN_NAMES,
    DETAILS_X_START,
    PRODUCT_IMG_H,
    PRODUCT_IMG_W,
    PRODUCT_IMG_X,
    PRODUCT_IMG_Y,
)


class ProductDetailsMixin:
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

    def add_packing_slip(self, item_data, product_data, item_count, total_items, pack_product=None, pack_name=None, pack_title=None):
        self.add_page(orientation='L')
        self._draw_header(item_data, product_data, item_count, total_items)
        self._draw_product_details(item_data, product_data, total_items, pack_title)
