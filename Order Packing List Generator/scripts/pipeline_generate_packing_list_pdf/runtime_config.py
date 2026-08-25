from pathlib import Path
from typing import Dict, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_POSITION_CODE = "X"
PROCESS_INFO_SHEET = "Process Info Sheet"
DEFAULT_WORKBOOK = PROJECT_ROOT / "Data" / "Workbook.xlsx"
BACK_PRINT_REFERENCE_IMAGE = PROJECT_ROOT / "assets" / "Back Print.jpg"

MAX_PAGES_PER_PDF = 50
IMAGE_DPI = 96

IMAGE_CACHE: Dict[Tuple[str, int, int], bytes] = {}
URL_IMAGE_CACHE: Dict[Tuple[str, int, int], Optional[bytes]] = {}
URL_IMAGE_TIMEOUT_SEC = 3
URL_IMAGE_MAX_BYTES = 8 * 1024 * 1024
