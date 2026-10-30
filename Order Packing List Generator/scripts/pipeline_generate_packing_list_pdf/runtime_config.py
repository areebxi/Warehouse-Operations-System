from pathlib import Path
import sys
from typing import Dict, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

DEFAULT_POSITION_CODE = "X"
PROCESS_INFO_SHEET = "Process Info Sheet"
DEFAULT_WORKBOOK = wh.packing_workbook_path()
# ponytail: DB path first; legacy app assets/ until all machines migrate
_BACK_PRINT_DB = wh.packing_back_print_path()
_BACK_PRINT_LEGACY = PROJECT_ROOT / "assets" / "Back Print.jpg"
BACK_PRINT_REFERENCE_IMAGE = (
    _BACK_PRINT_DB if _BACK_PRINT_DB.is_file() else _BACK_PRINT_LEGACY
)

MAX_PAGES_PER_PDF = 50
IMAGE_DPI = 96

IMAGE_CACHE: Dict[Tuple[str, int, int], bytes] = {}
URL_IMAGE_CACHE: Dict[Tuple[str, int, int], Optional[bytes]] = {}
URL_IMAGE_TIMEOUT_SEC = 3
URL_IMAGE_MAX_BYTES = 8 * 1024 * 1024
