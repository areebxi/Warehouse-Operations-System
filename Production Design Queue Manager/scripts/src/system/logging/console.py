"""Console log capture setup/teardown utilities."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

_console_logs_dir: Optional[Path] = None
_console_log_file: Optional[Any] = None
_original_stdout = None
_original_stderr = None

_console_log_stats = {
    'errors': 0,
    'warnings': 0,
    'exceptions': 0,
    'error_dialogs': 0,
    'warning_dialogs': 0,
    'tracebacks': 0,
    'start_time': None,
    'end_time': None
}


def get_console_logs_dir() -> Optional[Path]:
    return _console_logs_dir


def get_console_log_stats() -> Dict[str, Any]:
    return _console_log_stats


def _get_project_root() -> Path:
    """Resolve repository root from scripts/src/system/logging module path."""
    return Path(__file__).resolve().parents[4]


def _safe_stream_write(stream, message: str) -> None:
    """Write to a stream if it exists; ignore missing/broken consoles (e.g. pythonw)."""
    if stream is None or not hasattr(stream, "write"):
        return
    try:
        stream.write(message)
        if hasattr(stream, "flush"):
            stream.flush()
    except Exception:
        pass


def _safe_stream_flush(stream) -> None:
    """Flush a stream if it exists; ignore missing/broken consoles."""
    if stream is None or not hasattr(stream, "flush"):
        return
    try:
        stream.flush()
    except Exception:
        pass


def setup_console_logging() -> Optional[Path]:
    """Setup console logging to capture all stdout/stderr output to a file."""
    global _console_logs_dir, _console_log_file, _original_stdout, _original_stderr

    if hasattr(setup_console_logging, '_initialized'):
        return _console_log_file.name if _console_log_file else None
    setup_console_logging._initialized = True

    try:
        project_root = _get_project_root()

        _console_logs_dir = project_root / "Logs"
        _console_logs_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"console_log_{timestamp}.txt"
        log_path = _console_logs_dir / log_filename

        _console_log_file = open(log_path, 'w', encoding='utf-8', buffering=1)

        _console_log_stats['start_time'] = datetime.now()
        _console_log_stats['errors'] = 0
        _console_log_stats['warnings'] = 0
        _console_log_stats['exceptions'] = 0
        _console_log_stats['error_dialogs'] = 0
        _console_log_stats['warning_dialogs'] = 0
        _console_log_stats['tracebacks'] = 0

        header = "=" * 80 + "\n"
        header += "QUEUE APP - CONSOLE LOG\n"
        header += "=" * 80 + "\n"
        header += f"Application Start Time: {_console_log_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"Log File: {log_filename}\n"
        header += "=" * 80 + "\n\n"
        _console_log_file.write(header)
        _console_log_file.flush()

        _original_stdout = sys.stdout
        _original_stderr = sys.stderr

        class Tee:
            def __init__(self, original_stream, log_file, stream_name):
                self.original_stream = original_stream
                self.log_file = log_file
                self.stream_name = stream_name

            def write(self, message):
                _safe_stream_write(self.original_stream, message)

                try:
                    if self.log_file and not self.log_file.closed and message:
                        # Keep blank lines as-is; prefix other lines with a
                        # timestamp unless they already look timestamped.
                        if message.strip() and not message.lstrip().startswith('['):
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            # Preserve leading newlines from callers that emit "\ntext"
                            leading = ""
                            body = message
                            while body.startswith("\n"):
                                leading += "\n"
                                body = body[1:]
                            self.log_file.write(f"{leading}[{timestamp}] {body}")
                        else:
                            self.log_file.write(message)
                        self.log_file.flush()
                except Exception as e:
                    _safe_stream_write(
                        self.original_stream,
                        f"[LOG ERROR] Failed to write to log file: {e}\n",
                    )
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

        sys.stdout = Tee(_original_stdout, _console_log_file, "STDOUT")
        sys.stderr = Tee(_original_stderr, _console_log_file, "STDERR")

        print(f"Console logging initialized. Log file: {log_path}")
        return log_path
    except Exception as e:
        _safe_stream_write(sys.__stderr__, f"CRITICAL: Failed to setup console logging: {e}\n")
        _safe_stream_write(sys.__stderr__, "Application will continue without console logging.\n")
        return None


def close_console_logging() -> None:
    """Close console log file and restore original stdout/stderr."""
    global _console_log_file, _original_stdout, _original_stderr, _console_log_stats

    try:
        if _console_log_file and not _console_log_file.closed:
            _console_log_stats['end_time'] = datetime.now()

            runtime = None
            if _console_log_stats['start_time'] and _console_log_stats['end_time']:
                runtime_delta = _console_log_stats['end_time'] - _console_log_stats['start_time']
                total_seconds = int(runtime_delta.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                if hours > 0:
                    runtime = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    runtime = f"{minutes}m {seconds}s"
                else:
                    runtime = f"{seconds}s"

            summary = "\n" + "=" * 80 + "\n"
            summary += "RUN SUMMARY REPORT\n"
            summary += "=" * 80 + "\n"
            summary += f"Application End Time: {_console_log_stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            if runtime:
                summary += f"Total Runtime: {runtime}\n"
            summary += "\n"
            summary += "ANOMALIES DETECTED:\n"
            summary += "-" * 80 + "\n"
            summary += f"  Total Errors:           {_console_log_stats['errors']}\n"
            summary += f"  Total Warnings:         {_console_log_stats['warnings']}\n"
            summary += f"  Unhandled Exceptions:   {_console_log_stats['exceptions']}\n"
            summary += f"  Error Dialogs:          {_console_log_stats['error_dialogs']}\n"
            summary += f"  Warning Dialogs:        {_console_log_stats['warning_dialogs']}\n"
            summary += f"  Tracebacks:             {_console_log_stats['tracebacks']}\n"
            summary += "\n"

            total_anomalies = (
                _console_log_stats['errors'] +
                _console_log_stats['warnings'] +
                _console_log_stats['exceptions']
            )

            if total_anomalies == 0:
                summary += "STATUS: ✓ Run completed successfully with no anomalies detected.\n"
            elif _console_log_stats['exceptions'] > 0:
                summary += "STATUS: ✗ Run completed with CRITICAL issues (unhandled exceptions detected).\n"
            elif _console_log_stats['errors'] > 0:
                summary += "STATUS: ⚠ Run completed with ERRORS detected.\n"
            elif _console_log_stats['warnings'] > 0:
                summary += "STATUS: ⚠ Run completed with WARNINGS detected.\n"
            else:
                summary += "STATUS: ? Run completed (status unclear).\n"

            summary += "\n"
            summary += "NOTE: Logs for this run are saved in the Logs/ folder:\n"
            summary += "  - console_log_*.txt          (complete run output)\n"
            summary += "  - *size_determination_*.txt  (size reference per design)\n"
            summary += "\n"
            summary += "=" * 80 + "\n"

            _console_log_file.write(summary)
            _console_log_file.flush()
            _console_log_file.close()
            _safe_stream_write(sys.__stdout__, "\n" + summary)

        if _original_stdout:
            sys.stdout = _original_stdout
        if _original_stderr:
            sys.stderr = _original_stderr
    except Exception as e:
        try:
            if _original_stdout:
                sys.stdout = _original_stdout
            if _original_stderr:
                sys.stderr = _original_stderr
            _safe_stream_write(sys.__stderr__, f"Warning: Error closing console log: {e}\n")
        except Exception:
            pass
