"""Step 2 CL enrich constants + path defaults."""

from __future__ import annotations

import sys
from pathlib import Path

NEW_COLUMNS = [
    "Process and Item Number",
    "Gender Apparel",
    "Size",
    "Colour",
    "Picture Name",
    "Position",
    "Customise",
    "Prime",
    "Apparel Image",
    "Logo/Design Image",
]

# Map packing output columns -> candidate CL CSV headers (first present wins).
# Logo/Design Image has no CL CSV column — stays blank. Process and Item Number
# stays blank at Step 2 (Step 5 assigns).
CL_DB_COLUMN_ALIASES = {
    "Process and Item Number": ["Process and Item Number"],
    "Gender Apparel": ["Gender Apparel"],
    "Size": ["Size"],
    "Colour": ["Colour", "Colour Name", "Color"],
    "Picture Name": ["Apparel Image", "Picture Name"],
    "Position": ["Print Positions", "Position"],
    "Customise": ["Customise", "Customize"],
    "Prime": ["Amazon Prime", "Prime"],
    "Apparel Image": ["Apparel Image", "Apparel Picture"],
    "Logo/Design Image": ["Logo/Design Image", "Design Picture", "Logo/Design"],
}

CUSTOM_LABEL_COL = "Custom Label"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
from shared.cl_sku_match import default_cl_csv_path  # noqa: E402

DATA_DIR = wh.packing_data_dir()
DEFAULT_WORKBOOK = wh.packing_workbook_path()
DEFAULT_CL_CSV = default_cl_csv_path(PROJECT_ROOT)

_ITEM_NAME_CUSTOM_KEYWORDS = (
    "personalised",
    "personalized",
    "custom",
    "customisable",
    "customizable",
)

_ITEM_OPTIONS_CUSTOM_PHRASES = (
    "message if you do need customisation",
    "back print option",
)
