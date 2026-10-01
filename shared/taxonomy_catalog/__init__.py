"""Squeezed warehouse taxonomy for the four Areeb columns (Hashim #038).

Title Case. Product Type has no gender (Department holds that).
Product Style is a named range / simplified product name — never a supplier code.
"""

from shared.taxonomy_catalog.aliases import ALIASES
from shared.taxonomy_catalog.api import (
    bag_type_from_code,
    collapse_style,
    csv_rows,
    head_type_from_code,
    style_from_code,
)
from shared.taxonomy_catalog.code_maps import (
    BAG_TYPE_BY_CODE,
    HEAD_TYPE_BY_CODE,
    STYLE_BY_CODE,
)
from shared.taxonomy_catalog.dims import *
from shared.taxonomy_catalog.duplicates import TYPE_DUPLICATE_STYLES
from shared.taxonomy_catalog.style_phrases import STYLE_PHRASES
from shared.taxonomy_catalog.styles_list import PRODUCT_STYLES

__all__ = [name for name in dir() if name.isupper() or name in {
    "style_from_code",
    "bag_type_from_code",
    "head_type_from_code",
    "collapse_style",
    "csv_rows",
    "ALIASES",
    "STYLE_BY_CODE",
    "BAG_TYPE_BY_CODE",
    "HEAD_TYPE_BY_CODE",
    "STYLE_PHRASES",
    "TYPE_DUPLICATE_STYLES",
    "PRODUCT_STYLES",
    "DEFAULT_STYLE",
}]
