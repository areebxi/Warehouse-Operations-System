"""ponytail: watcher helper self-check — fails if PID path or script resolution drifts."""

from __future__ import annotations

from shared import design_queues_watcher as dqw
from shared import paths as wh


def main() -> None:
    script = dqw.watcher_script_path()
    assert script == wh.queue_app_dir() / "scripts" / "design_queues_watcher.py"
    assert script.is_file(), f"missing watcher script: {script}"
    pid_path = dqw.pid_file_path()
    assert pid_path.parent == wh.shared_inbox_dtf_des_root()
    assert pid_path.name == ".design_queues_watcher.pid"
    assert dqw.is_running() in (True, False)
    print("design_queues_watcher helper ok")


if __name__ == "__main__":
    main()
