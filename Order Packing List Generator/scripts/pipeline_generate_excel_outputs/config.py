import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

EXCEL_PROCESS_NO_DASH = False

REQUIRED = [
    "Order Number (Base)",
    "Item Quantity",
    "Item SKU",
    "Item Name",
    "Recipient Name",
    "Process and Item Number",
    "Gender Apparel",
    "Size",
    "Colour",
]

DTF_SKU_MAP_CSV = wh.packing_new_sku_csv_path()
DTF_COL_COMPANY_LABEL = "Company-Custom-Label"
DTF_COL_OLD_LABEL = "Old-Company-Custom-Label"
_DTF_DESIGN_HEAD_LG = re.compile(
    r"^([0-9A-Za-z]*\d+(?:LG|TSU|AV|HK))-(.*)$",
    re.IGNORECASE,
)
_DTF_DESIGN_HEAD_FAWAD = re.compile(
    r"^(fawad\d+)-(.*)$",
    re.IGNORECASE,
)
_DTF_DESIGN_HEAD_PER = re.compile(
    r"^([A-Za-z0-9]*\d+PER)-(.*)$",
    re.IGNORECASE,
)

