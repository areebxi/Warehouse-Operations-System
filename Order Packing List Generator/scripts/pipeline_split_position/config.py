from pathlib import Path
import sys

REQUIRED_COLUMNS = ["Gender Apparel", "Position"]
PROCESS_INFO_SHEET = "Process Info Sheet"
MULTIPLE_POSITIONS_SHEET = "Multiple Positions"
LOGO_IDS_TO_POSITIONS_SHEET = "Logo IDs to Positions"
DEFAULT_POSITION_LABEL = "Default Position"

# Logo IDs to Positions: column headers for lookup
LIP_LOGO_ID_COL = "Logo IDs"
LIP_POSITION_COL = "Positions"

# Multiple Positions: column for lookup and position columns (order matters)
DP_ABBREVIATION_COL = "abbreviation"
DP_POSITION_COLS = ["position-1", "position-2", "position-3", "position-4", "position-5"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
DEFAULT_WORKBOOK = wh.packing_workbook_path()
DEFAULT_OUTPUT_DIR = wh.packing_output_dir()
PREFIX_STEP3 = "3_fill_prime_and_images_"
SCRIPT_NAME = "split_and_assign_position_codes"

# Fallback when Process Info Sheet has "Position Combination 1" etc. but not position text.
# Normalized key -> code. Sheet rows override these if they use the same position text.
DEFAULT_POSITION_TEXT_TO_CODE = {
    "front top center, back top center": "X1",
    "front top center": "X2",
    "back top center": "X3",
    "front, pocket": "X4",
}

