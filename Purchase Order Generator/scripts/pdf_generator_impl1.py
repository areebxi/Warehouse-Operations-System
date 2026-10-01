from __future__ import annotations
import pandas as pd
from fpdf import FPDF
from pathlib import Path
from datetime import date
from app_paths import APP_ROOT, asset_path, data_path, packs_database_path, product_database_path, tag_output_dir
from pdf_generator_impl1_mixin1 import PDFMixin1
from pdf_generator_impl1_mixin2 import PDFMixin2

class PDF(PDFMixin1, PDFMixin2, FPDF):
    """Generates one packing slip page per item."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force built-in Helvetica (ASCII) to avoid any machine-specific font paths.
        self.base_font = 'Helvetica'
        self._supports_unicode = False
        self.set_font(self.base_font, '', 12)


