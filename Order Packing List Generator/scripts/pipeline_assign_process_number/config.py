from pathlib import Path

REQUIRED_COLUMNS = [
    "Gender Apparel",
    "Prime",
    "Customise",
    "Ship By",
    "Position Code",
    "Process and Item Number",
]
# When separate_by_logo_id is True, step-4 must also have "Logo ID" and "Order Number"
LOGO_ID_REQUIRED_COLUMNS = ["Logo ID", "Order Number"]
PROCESS_INFO_SHEET = "Process Info Sheet"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output"
PREFIX_STEP4 = "4_matched_split_and_assign_position_codes_"
SCRIPT_NAME = "assign_process_number"

# Column indices (0-based) for Process Info Sheet: A=0, B=1, D=3, E=4 (Gender Apparel, Process Start, Shift, Code)
COL_GENDER_APPAREL = 0
COL_PROCESS_START = 1
COL_SHIFT_LABEL = 3
COL_SHIFT_CODE = 4

# Fallbacks: shift from user input; position when empty
SHIFT_FALLBACK = {"1st": "A", "2nd": "B", "3rd": "C", "4th": "D", "5th": "E"}
POSITION_FALLBACK = "X"

