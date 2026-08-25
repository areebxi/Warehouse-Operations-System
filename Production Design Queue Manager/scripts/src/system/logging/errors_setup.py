"""Global error-hook setup logic (stats only; no Errors and Warnings files)."""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from .console import get_console_log_stats, get_console_logs_dir

_logs_dir: Optional[Path] = None
_console_log_stats = get_console_log_stats()


def _get_project_root() -> Path:
    """Resolve repository root from scripts/src/system/logging module path."""
    return Path(__file__).resolve().parents[4]


def setup_error_logging() -> Tuple[None, Optional[Path]]:
    """Setup error/warning hooks that feed the console log and run stats."""
    global _logs_dir

    if hasattr(setup_error_logging, '_initialized'):
        return None, _logs_dir
    setup_error_logging._initialized = True

    project_root = _get_project_root()
    console_dir = get_console_logs_dir()
    _logs_dir = console_dir if console_dir is not None else (project_root / "Logs")
    try:
        _logs_dir.mkdir(exist_ok=True)
        print(f"Logging system initialized. Logs will be saved to: {_logs_dir}")
    except Exception as e:
        print(f"Warning: Could not create Logs folder: {e}")
        _logs_dir = None

    def global_exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        _console_log_stats['exceptions'] += 1
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try:
            if sys.__stderr__ is not None and hasattr(sys.__stderr__, "write"):
                sys.__stderr__.write(f"\n{'='*80}\nUNHANDLED EXCEPTION OCCURRED!\n")
                sys.__stderr__.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                sys.__stderr__.write(f"Exception Type: {exc_type.__name__}\nException Value: {exc_value}\n{'='*80}\n")
                sys.__stderr__.write(error_msg + f"{'='*80}\n\n")
                if hasattr(sys.__stderr__, "flush"):
                    sys.__stderr__.flush()
        except Exception:
            pass

    sys.excepthook = global_exception_handler
    original_print = print

    def logged_print(*args, **kwargs):
        message = ' '.join(str(arg) for arg in args)
        original_print(*args, **kwargs)
        if "[ANOMALY DETECTED]" in message:
            return
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in ['error', 'exception', 'failed', 'fail']):
            _console_log_stats['errors'] += 1
        elif 'warning' in message_lower:
            _console_log_stats['warnings'] += 1

    import builtins
    builtins.print = logged_print

    class StderrLogger:
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
            self.buffer = ""

        def _write_original(self, message):
            stream = self.original_stderr
            if stream is None or not hasattr(stream, "write"):
                return
            try:
                stream.write(message)
                if hasattr(stream, "flush"):
                    stream.flush()
            except Exception:
                pass

        def write(self, message):
            if not message.strip():
                return
            if "[ANOMALY DETECTED]" in message:
                self._write_original(message)
                return
            self._write_original(message)
            self.buffer += message
            if '\n' in message and ('Traceback' in self.buffer or 'File "' in self.buffer) and self.buffer.strip().endswith(')'):
                _console_log_stats['tracebacks'] += 1
                _console_log_stats['errors'] += 1
                self.buffer = ""
            elif len(self.buffer) > 200:
                _console_log_stats['errors'] += 1
                self.buffer = ""

        def flush(self):
            stream = self.original_stderr
            if stream is not None and hasattr(stream, "flush"):
                try:
                    stream.flush()
                except Exception:
                    pass
            if self.buffer.strip():
                _console_log_stats['errors'] += 1
                self.buffer = ""

    current_stderr = sys.stderr if sys.stderr != sys.__stderr__ else sys.__stderr__
    sys.stderr = StderrLogger(current_stderr)

    from tkinter import messagebox
    _original_showerror = messagebox.showerror
    _original_showwarning = messagebox.showwarning

    def logged_showerror(title, message, **kwargs):
        _console_log_stats['error_dialogs'] += 1
        _console_log_stats['errors'] += 1
        print(f"Error dialog — {title}: {message}")
        return _original_showerror(title, message, **kwargs)

    def logged_showwarning(title, message, **kwargs):
        _console_log_stats['warning_dialogs'] += 1
        _console_log_stats['warnings'] += 1
        print(f"Warning dialog — {title}: {message}")
        return _original_showwarning(title, message, **kwargs)

    messagebox.showerror = logged_showerror
    messagebox.showwarning = logged_showwarning
    return None, _logs_dir
