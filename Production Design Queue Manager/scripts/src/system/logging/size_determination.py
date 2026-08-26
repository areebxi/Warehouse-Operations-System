"""Size-determination log buffering and file persistence."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

_size_determination_logs_dir: Optional[Path] = None
_size_determination_log_buffer: List[str] = []
_current_log_file_path: Optional[Path] = None

_SUMMARY_LABELS = {
    "total_designs": "Total designs",
    "size_reference_used": "Designs using size reference",
    "original_dimensions_used": "Designs using original dimensions",
    "resized": "Designs resized",
    "single_designs": "Single designs",
    "double_designs": "Double designs",
    "pocket_overrides": "Pocket overrides",
    "sleeve_overrides": "Sleeve overrides",
    "canvas_scaled": "Canvas scaled",
    "personalised_found": "Personalised designs found",
    "all_in_one_found": "All-in-one designs found",
}


def _get_project_root() -> Path:
    """Resolve repository root from scripts/src/system/logging module path."""
    return Path(__file__).resolve().parents[4]


def initialize_size_determination_logging() -> Optional[Path]:
    """Use the shared Logs directory for size determination files."""
    global _size_determination_logs_dir
    if _size_determination_logs_dir is None:
        project_root = _get_project_root()
        import sys
        warehouse = project_root.parent
        if str(warehouse) not in sys.path:
            sys.path.insert(0, str(warehouse))
        from shared import paths as wh
        _size_determination_logs_dir = wh.queue_logs_dir()
        try:
            _size_determination_logs_dir.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create Logs folder: {e}")
            _size_determination_logs_dir = None
    return _size_determination_logs_dir


def start_size_determination_log(
    input_file_path: Optional[str] = None,
    processing_mode: str = "standard",
) -> Optional[Path]:
    """Start a new size determination log session for a processing run."""
    global _size_determination_log_buffer, _current_log_file_path
    _size_determination_log_buffer = []

    log_dir = initialize_size_determination_logging()
    if log_dir is None:
        _current_log_file_path = None
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if input_file_path:
        input_stem = os.path.splitext(os.path.basename(input_file_path))[0]
        filename = f"({input_stem}) size_determination_{timestamp}.txt"
    else:
        filename = f"size_determination_{timestamp}.txt"

    _current_log_file_path = log_dir / filename

    mode_label = processing_mode.replace("_", " ").title()
    header = "=" * 80 + "\n"
    header += "SIZE DETERMINATION LOG\n"
    header += "=" * 80 + "\n"
    header += f"Started:          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"Processing Mode:  {mode_label}\n"
    if input_file_path:
        header += f"Input File:       {os.path.basename(input_file_path)}\n"
        header += f"Input File Path:  {input_file_path}\n"
    header += "=" * 80 + "\n\n"

    _size_determination_log_buffer.append(header)
    return _current_log_file_path


def log_size_determination(entry: str) -> None:
    """Append a size determination log entry to the buffer."""
    if _size_determination_log_buffer is not None:
        _size_determination_log_buffer.append(entry)


def finish_size_determination_log(summary_stats: Optional[Dict[str, Any]] = None) -> None:
    """Write buffered size determination entries to disk and clear the buffer."""
    global _size_determination_log_buffer, _current_log_file_path

    if _current_log_file_path is None or not _size_determination_log_buffer:
        _size_determination_log_buffer = []
        _current_log_file_path = None
        return

    try:
        if summary_stats:
            _size_determination_log_buffer.append("\n" + "=" * 80 + "\n")
            _size_determination_log_buffer.append("SUMMARY\n")
            _size_determination_log_buffer.append("=" * 80 + "\n")
            for key, value in summary_stats.items():
                label = _SUMMARY_LABELS.get(key, key.replace("_", " ").title())
                _size_determination_log_buffer.append(f"{label}: {value}\n")

        with open(_current_log_file_path, "w", encoding="utf-8") as f:
            f.writelines(_size_determination_log_buffer)
    except Exception as e:
        print(f"Warning: Could not write size determination log: {e}")
    finally:
        _size_determination_log_buffer = []
        _current_log_file_path = None
