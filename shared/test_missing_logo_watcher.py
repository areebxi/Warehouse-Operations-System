"""ponytail: watcher helper self-check — fails if PID path or script resolution drifts."""

from __future__ import annotations

from shared import missing_logo_watcher as mlw
from shared import paths as wh


def main() -> None:
    script = mlw.watcher_script_path()
    assert script == wh.queue_app_dir() / "scripts" / "auto_missing_logo_watcher.py"
    assert script.is_file(), f"missing watcher script: {script}"
    pid_path = mlw.pid_file_path()
    assert pid_path.parent == wh.shared_inbox_dtf_des_root()
    assert mlw.is_running() in (True, False)
    print("missing_logo_watcher helper ok")


if __name__ == "__main__":
    main()
