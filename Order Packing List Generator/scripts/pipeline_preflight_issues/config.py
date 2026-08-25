from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_WORKBOOK = PROJECT_ROOT / "Data" / "Workbook.xlsx"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Unmatched SKU Files"
CONFIG_DIR = PROJECT_ROOT / "config"
PREFLIGHT_CONFIG = CONFIG_DIR / "preflight_issues_config.json"
# Legacy config path (read as fallback; writes go to PREFLIGHT_CONFIG only)
UNMATCHED_CONFIG = CONFIG_DIR / "unmatched_skus_config.json"

NO_ISSUES = object()
NO_UNMATCHED = NO_ISSUES  # alias for compatibility

