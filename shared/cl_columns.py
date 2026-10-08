"""Live Custom Label CSV column names (NocoDB underscored export).

Locked 2026-10-04: warehouse reads these headers; exporter does not remap.
Stand-ins:
  BTC SKU      → Supplier_SKU
  Supply Method → Stock_Type (values normalized via shared.supply_method.normalize_stock_type)
Areeb taxonomy columns keep spaces: Category (Areeb), …
"""

from __future__ import annotations

# Match key
CUSTOM_LABEL = "Custom_Label"

# Core garment / print fields
GENDER_APPAREL = "Gender_Apparel"
COLOUR = "Colour"
SIZE = "Size"
APPAREL_IMAGE = "Apparel_Image"
PRINT_POSITIONS = "Print_Positions"
CUSTOMISE = "Customise"
AMAZON_PRIME = "Amazon_Prime"
PRINT_POSITION_CODE = "Print_Position_Code"
PRINTING_TYPE = "Printing_Type"
DESIGN_TYPE = "Design_Type"
BRAND = "Brand"

# Supplier / stock (NocoDB names)
SUPPLIER_NAME = "Supplier_Name"
SUPPLIER_SKU = "Supplier_SKU"
SUPPLIER_PRODUCT_CODE = "Supplier_Product_Code"
WAREHOUSE_SKU = "Warehouse_SKU"
STOCK_TYPE = "Stock_Type"

# Stand-ins for retired warehouse headers (supervisor 2026-10-04)
BTC_SKU = SUPPLIER_SKU  # was "BTC SKU"
SUPPLY_METHOD = STOCK_TYPE  # was "Supply Method"; values fixed later

# Areeb taxonomy (still spaced with parentheses in NocoDB)
CATEGORY_AREEB = "Category (Areeb)"
PRODUCT_TYPE_AREEB = "Product Type (Areeb)"
PRODUCT_STYLE_AREEB = "Product Style (Areeb)"
DEPARTMENT_AREEB = "Department (Areeb)"


def width_mm(n: int) -> str:
    return f"Width_{n}_mm"


def height_mm(n: int) -> str:
    return f"Height_{n}_mm"


def position_name(n: int) -> str:
    return f"Position_{n}_Name"


def print_size(n: int) -> str:
    return f"Print_Size_{n}"


def legacy_header_aliases() -> dict[str, str]:
    """Areeb-era spaced CSV headers → NocoDB names in this module."""
    aliases = {
        "Custom Label": CUSTOM_LABEL,
        "Gender Apparel": GENDER_APPAREL,
        "Apparel Image": APPAREL_IMAGE,
        "Print Positions": PRINT_POSITIONS,
        "Amazon Prime": AMAZON_PRIME,
        "Print Position Code": PRINT_POSITION_CODE,
        "Printing Type": PRINTING_TYPE,
        "Design Type": DESIGN_TYPE,
        "Supplier Name": SUPPLIER_NAME,
        "Supplier SKU": SUPPLIER_SKU,
        "Supplier Product Code": SUPPLIER_PRODUCT_CODE,
        "Warehouse SKU": WAREHOUSE_SKU,
        "Supply Method": SUPPLY_METHOD,
        "Stock Type": STOCK_TYPE,
    }
    for n in range(1, 5):
        aliases[f"Width {n} (mm)"] = width_mm(n)
        aliases[f"Height {n} (mm)"] = height_mm(n)
        aliases[f"Position {n} Name"] = position_name(n)
        aliases[f"Print Size {n}"] = print_size(n)
    return aliases


def rename_legacy_headers(columns: list[str]) -> dict[str, str]:
    """Map present legacy headers to NocoDB names when the NocoDB name is absent."""
    aliases = legacy_header_aliases()
    present = set(columns)
    return {
        src: dst
        for src, dst in aliases.items()
        if src in present and dst not in present
    }


def normalize_cl_record(row: dict, rename: dict[str, str]) -> dict:
    """Rewrite one CSV record onto NocoDB header names. No-op when rename is empty."""
    if not rename:
        return row
    return {
        rename.get(key, key): value
        for key, value in row.items()
        if key is not None
    }
