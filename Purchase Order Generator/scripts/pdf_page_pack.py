"""Pack-of-N slip drawing for packing slips."""
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


class PackSlipMixin:
    def add_pack_slip(self, item_data, component_products, item_count, total_items, pack_product=None, pack_name=None, pack_title=None):
        """Render Pack of N in the same layout as single item: composite thumbnails inside the main image box, and full details on the right.

        pack_product: details row for the PACK SKU itself (used for Pack Name, etc.)
        """
        self.add_page(orientation='L')

        # Use first component as representative for header/details
        main_product = component_products[0] if component_products else {}
        # Draw standard header (process + order id + brand logo)
        self._draw_header(item_data, main_product, item_count, total_items)

        # Draw composite thumbnails within the image box region
        box_x = PRODUCT_IMG_X
        box_y = PRODUCT_IMG_Y
        box_w = PRODUCT_IMG_W
        # Make the thumbnail area taller for packs so images appear larger
        pack_size = len(component_products)
        if pack_size >= 5:
            box_h = PRODUCT_IMG_H + 40
        elif pack_size >= 3:
            box_h = PRODUCT_IMG_H + 20
        else:
            box_h = PRODUCT_IMG_H

        pack_size = len(component_products)
        cols = 2 if pack_size > 2 else pack_size  # 1xN for 1-2, 2xN for more
        rows = (pack_size + cols - 1) // cols if cols else 1
        gap = 3
        thumb_w = (box_w - (cols - 1) * gap) / max(1, cols)
        # Reserve space below each thumbnail for label: Colour, Size, Qty
        label_h = 8
        label_gap = 2
        thumb_h = ((box_h - (rows - 1) * gap) / max(1, rows)) - (label_h + label_gap)

        # Parse component colours from CSV if available
        colours_raw = item_data.get(COLUMN_NAMES['component_colours'], '')
        component_colours = []
        if isinstance(colours_raw, str) and colours_raw.strip():
            component_colours = [c.strip() for c in colours_raw.split(',') if c.strip()]
        
        _colour_img_by_uid = _load_colour_image_basenames_by_uid()

        def _find_component_image(product_filename, sku_value):
            return _resolve_product_image_path(
                product_filename, sku_value, colour_img_by_uid=_colour_img_by_uid
            )

        for idx, comp in enumerate(component_products):
            r = idx // cols
            c = idx % cols
            x = box_x + c * (thumb_w + gap)
            # Include label height and gap in row spacing so labels are not overlapped by next row images
            y = box_y + r * (thumb_h + label_h + label_gap + gap)
            img_filename = comp.get(COLUMN_NAMES['product_image_filename'])
            img_sku = comp.get(COLUMN_NAMES['db_sku'])
            img_path, _, _ = _find_component_image(img_filename, img_sku)
            if img_path:
                self._place_image(str(img_path), x=x, y=y, w=thumb_w, h=thumb_h)
            
            # Draw label under the image: Colour Size xQty (always draw, even if no image)
            # Use CSV colours if available, otherwise fallback to database colour
            if idx < len(component_colours):
                colour_text = component_colours[idx]
            else:
                colour_text = str(comp.get(COLUMN_NAMES['colour'], '') or '')
            size_text = str(comp.get(COLUMN_NAMES['size'], '') or '')
            qty_text = str(item_data.get(COLUMN_NAMES['quantity'], ''))
            label_text_parts = []
            if colour_text:
                label_text_parts.append(colour_text)
            if size_text:
                label_text_parts.append(size_text)
            if qty_text:
                label_text_parts.append(f"x{qty_text}")
            label_text = " ".join(label_text_parts)
            if label_text:
                self.set_xy(x, y + thumb_h + label_gap)
                self.set_font(self.base_font, 'B', 10)
                # Centered label within the thumbnail width
                self.cell(w=thumb_w, h=label_h, txt=self._t(label_text), border=0, align='C')

        # Recipient under the enlarged image box (wrapped to avoid cutting long names)
        name_y_pos = PRODUCT_IMG_Y + box_h + 3
        self.set_xy(PRODUCT_IMG_X, name_y_pos)
        # Slightly smaller font so two lines can fit if needed
        self.set_font(self.base_font, 'B', 20)
        self.multi_cell(w=PRODUCT_IMG_W, h=8, txt=self._t(item_data.get(COLUMN_NAMES['recipient'], 'N/A')), border=0, align='C')

        # Details on the right, same structure as single item, but showing pack context
        self.set_xy(DETAILS_X_START, PRODUCT_IMG_Y)
        def write_detail(label, value):
            self.set_font(self.base_font, 'B', 12)
            self.set_x(DETAILS_X_START)
            self.cell(w=40, h=8, txt=self._t(label), border=0)
            self.set_font(self.base_font, '', 12)
            self.multi_cell(w=0, h=8, txt=self._t(f": {value}"), border=0)

        # Use pack_title from Packs Database.xlsx Column AI if available, otherwise fallback to Description
        title_value = pack_title if pack_title and str(pack_title).strip() else str(main_product.get(COLUMN_NAMES['description'], 'N/A'))
        write_detail('Title', title_value)

        # Directly under Title, show Pack Name from the PACK SKU row (database column for pack name)
        if pack_name and str(pack_name).strip():
            write_detail('Pack Name', str(pack_name))
        elif isinstance(pack_product, dict):
            # Try common column names for pack name; fall back gracefully
            candidate_keys = [
                'Pack Name', 'Pack', 'Package Name', 'Package', 'PackTitle', 'Title (Pack)'
            ]
            pack_name_value = None
            for key in candidate_keys:
                if key in pack_product and str(pack_product.get(key, '')).strip():
                    pack_name_value = str(pack_product.get(key))
                    break
            # As a last resort, reuse Description from pack row (may contain name)
            if not pack_name_value and COLUMN_NAMES['description'] in pack_product:
                pack_name_value = str(pack_product.get(COLUMN_NAMES['description']))
            if pack_name_value:
                write_detail('Pack Name', pack_name_value)
        # For PACK slips, omit Colour per request; keep Size
        write_detail('Size', str(main_product.get(COLUMN_NAMES['size'], 'N/A')))
        
        # Quantity styled like "Merge Order" pill if greater than 1
        quantity_value = str(item_data.get(COLUMN_NAMES['quantity'], 'N/A'))
        try:
            qty_num = int(quantity_value) if quantity_value.isdigit() else 0
            if qty_num > 1:
                self.set_x(DETAILS_X_START)
                pill_text = self._t(f"Quantity: {quantity_value}")
                self.set_font(self.base_font, 'B', 14)
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

        write_detail('Our SKU', str(item_data.get(COLUMN_NAMES['sku'], 'N/A')))  # pack sku
        write_detail('Brand', str(main_product.get(COLUMN_NAMES['brand'], 'N/A')))
        write_detail('Product Code', str(main_product.get(COLUMN_NAMES['product_code'], 'N/A')))
        write_detail('Package', f"Pack of {pack_size}")

        # Components list: show colours if provided; fallback to SKUs
        colours_raw = item_data.get(COLUMN_NAMES['component_colours'], '')
        if isinstance(colours_raw, str) and colours_raw.strip():
            comp_list_text = colours_raw
        else:
            comp_list_text = ", ".join([str(c.get(COLUMN_NAMES['db_sku'], '')) for c in component_products])
        write_detail('Components', comp_list_text)
