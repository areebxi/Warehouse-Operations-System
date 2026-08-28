from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
DEFAULT_WORKBOOK = wh.packing_workbook_path()
DEFAULT_CL_CSV = wh.cl_csv_path()
DEFAULT_OUTPUT_DIR = wh.packing_runtime_dir() / "Unmatched SKU Files"
CONFIG_DIR = wh.packing_config_dir()
PREFLIGHT_CONFIG = CONFIG_DIR / "preflight_issues_config.json"
# Legacy config path (read as fallback; writes go to PREFLIGHT_CONFIG only)
UNMATCHED_CONFIG = CONFIG_DIR / "unmatched_skus_config.json"

NO_ISSUES = object()
NO_UNMATCHED = NO_ISSUES  # alias for compatibility

