import re
from pathlib import Path
import sys

REQUIRED_COLUMNS = ["Process and Item Number", "Size", "Order Number", "Colour"]
PROCESS_INFO_SHEET = "Process Info Sheet"
SEQUENCE_BY_SIZE_HEADER = "Sequence by Size"
COL_AD_INDEX = 29  # Excel column AD = 0-based index 29

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
DEFAULT_OUTPUT_DIR = wh.packing_output_dir()
DEFAULT_WORKBOOK = wh.packing_workbook_path()
BLANK_FILENAME = "_blank"

PROCESS_TRACKER_SHEET = "Process Number Tracker"
TRACKER_SEQUENCE_START = 10000

# Windows-invalid filename characters
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')

