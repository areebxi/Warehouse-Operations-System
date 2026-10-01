"""Stop console tee logging and write the run summary footer."""
from __future__ import annotations

import sys
from datetime import datetime

from . import console_state as st
from .console_state import _safe_stream_write


def close_console_logging() -> None:
    """Close console log file and restore original stdout/stderr."""
    try:
        if st._console_log_file and not st._console_log_file.closed:
            stats = st._console_log_stats
            stats["end_time"] = datetime.now()
            runtime = None
            if stats["start_time"] and stats["end_time"]:
                total_seconds = int((stats["end_time"] - stats["start_time"]).total_seconds())
                hours, rem = divmod(total_seconds, 3600)
                minutes, seconds = divmod(rem, 60)
                if hours > 0:
                    runtime = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    runtime = f"{minutes}m {seconds}s"
                else:
                    runtime = f"{seconds}s"

            summary = "\n" + "=" * 80 + "\nRUN SUMMARY REPORT\n" + "=" * 80 + "\n"
            summary += f"Application End Time: {stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            if runtime:
                summary += f"Total Runtime: {runtime}\n"
            summary += "\nANOMALIES DETECTED:\n" + "-" * 80 + "\n"
            summary += f"  Total Errors:           {stats['errors']}\n"
            summary += f"  Total Warnings:         {stats['warnings']}\n"
            summary += f"  Unhandled Exceptions:   {stats['exceptions']}\n"
            summary += f"  Error Dialogs:          {stats['error_dialogs']}\n"
            summary += f"  Warning Dialogs:        {stats['warning_dialogs']}\n"
            summary += f"  Tracebacks:             {stats['tracebacks']}\n\n"
            total = stats["errors"] + stats["warnings"] + stats["exceptions"]
            if total == 0:
                summary += "STATUS: ✓ Run completed successfully with no anomalies detected.\n"
            elif stats["exceptions"] > 0:
                summary += "STATUS: ✗ Run completed with CRITICAL issues (unhandled exceptions detected).\n"
            elif stats["errors"] > 0:
                summary += "STATUS: ⚠ Run completed with ERRORS detected.\n"
            elif stats["warnings"] > 0:
                summary += "STATUS: ⚠ Run completed with WARNINGS detected.\n"
            else:
                summary += "STATUS: ? Run completed (status unclear).\n"
            summary += "\nNOTE: Logs for this run are saved in the Logs/ folder:\n"
            summary += "  - console_log_*.txt          (complete run output)\n"
            summary += "  - *size_determination_*.txt  (size reference per design)\n\n"
            summary += "=" * 80 + "\n"
            st._console_log_file.write(summary)
            st._console_log_file.flush()
            st._console_log_file.close()
            _safe_stream_write(sys.__stdout__, "\n" + summary)

        if st._original_stdout:
            sys.stdout = st._original_stdout
        if st._original_stderr:
            sys.stderr = st._original_stderr
    except Exception as e:
        try:
            if st._original_stdout:
                sys.stdout = st._original_stdout
            if st._original_stderr:
                sys.stderr = st._original_stderr
            _safe_stream_write(sys.__stderr__, f"Warning: Error closing console log: {e}\n")
        except Exception:
            pass
