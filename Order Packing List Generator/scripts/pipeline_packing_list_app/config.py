import os
import sys
from pathlib import Path

_PROJECT_ROOT_DEV = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = _PROJECT_ROOT_DEV
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402


def logs_directory() -> Path:
    """Directory for pipeline session logs (always writable when possible).

    - Normal runs: packing app ``Logs/``.
    - Frozen / one-file builds: try ``<exe_dir>/logs``, then ``%LOCALAPPDATA%/PackingListApp/logs``.
    """
    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).resolve().parent
        candidates = [
            exe_parent / "logs",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "PackingListApp" / "logs",
        ]
        for c in candidates:
            try:
                c.mkdir(parents=True, exist_ok=True)
                probe = c / ".write_probe"
                probe.write_text("", encoding="utf-8")
                probe.unlink(missing_ok=True)
                return c.resolve()
            except OSError:
                continue
        out = exe_parent / "logs"
        out.mkdir(parents=True, exist_ok=True)
        return out.resolve()
    return wh.packing_logs_dir().resolve()


DEFAULT_OUTPUT_DIR = wh.packing_output_dir()
DEFAULT_WORKBOOK = wh.packing_workbook_path()
DEFAULT_CL_CSV = wh.cl_csv_path()
CONFIG_DIR = wh.packing_config_dir()
CONFIG_PATH = wh.packing_gui_config_path()

CONFIG_KEYS = (
    "input_csv",
    "date",
    "shift",
    "output_dir",
    "workbook_path",
    "cl_csv_path",
    "apparel_dir",
    "logo_normal_dir",
    "logo_custom_single_dir",
    "logo_custom_double_dir",
    "pdf_copy_dir",
    "excel_copy_dir",
    "separate_by_logo_id",
    "logo_id_threshold",
    "use_fixed_process_number",
    "fixed_process_number",
    "run_missing_logo_pipeline",
    "use_demo_images",
    "input_mode",
    "shipstation_tag_name",
    "shipstation_tag_id",
    "shipstation_tags",
)
