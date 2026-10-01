"""Start console tee logging into Logs/console_log_*.txt."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import console_state as st
from .console_state import _get_project_root, _safe_stream_flush, _safe_stream_write


def setup_console_logging() -> Optional[Path]:
    """Setup console logging to capture all stdout/stderr output to a file."""
    if hasattr(setup_console_logging, "_initialized"):
        return st._console_log_file.name if st._console_log_file else None
    setup_console_logging._initialized = True

    try:
        project_root = _get_project_root()
        import sys as _sys_wh

        _wh_root = project_root.parent
        if str(_wh_root) not in _sys_wh.path:
            _sys_wh.path.insert(0, str(_wh_root))
        from shared import paths as wh

        st._console_logs_dir = wh.queue_logs_dir()
        st._console_logs_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"console_log_{timestamp}.txt"
        log_path = st._console_logs_dir / log_filename
        st._console_log_file = open(log_path, "w", encoding="utf-8", buffering=1)

        stats = st._console_log_stats
        stats["start_time"] = datetime.now()
        for k in ("errors", "warnings", "exceptions", "error_dialogs", "warning_dialogs", "tracebacks"):
            stats[k] = 0

        header = "=" * 80 + "\nQUEUE APP - CONSOLE LOG\n" + "=" * 80 + "\n"
        header += f"Application Start Time: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"Log File: {log_filename}\n" + "=" * 80 + "\n\n"
        st._console_log_file.write(header)
        st._console_log_file.flush()

        st._original_stdout = sys.stdout
        st._original_stderr = sys.stderr

        class Tee:
            def __init__(self, original_stream, log_file, stream_name):
                self.original_stream = original_stream
                self.log_file = log_file
                self.stream_name = stream_name

            def write(self, message):
                _safe_stream_write(self.original_stream, message)
                try:
                    if self.log_file and not self.log_file.closed and message:
                        if message.strip() and not message.lstrip().startswith("["):
                            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            leading, body = "", message
                            while body.startswith("\n"):
                                leading += "\n"
                                body = body[1:]
                            self.log_file.write(f"{leading}[{ts}] {body}")
                        else:
                            self.log_file.write(message)
                        self.log_file.flush()
                except Exception as e:
                    _safe_stream_write(self.original_stream, f"[LOG ERROR] Failed to write to log file: {e}\n")
                    _safe_stream_write(self.original_stream, message)

            def flush(self):
                _safe_stream_flush(self.original_stream)
                try:
                    if self.log_file and not self.log_file.closed:
                        self.log_file.flush()
                except Exception:
                    pass

            def close(self):
                if self.log_file and not self.log_file.closed:
                    self.log_file.close()

        sys.stdout = Tee(st._original_stdout, st._console_log_file, "STDOUT")
        sys.stderr = Tee(st._original_stderr, st._console_log_file, "STDERR")
        print(f"Console logging initialized. Log file: {log_path}")
        return log_path
    except Exception as e:
        _safe_stream_write(sys.__stderr__, f"CRITICAL: Failed to setup console logging: {e}\n")
        _safe_stream_write(sys.__stderr__, "Application will continue without console logging.\n")
        return None
