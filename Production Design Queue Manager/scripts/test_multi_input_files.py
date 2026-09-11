"""Self-check: multi-file input path resolution for Queue GUI."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gui_helpers.processing.gui_processing_helpers_folder import get_selected_input_files


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        a = os.path.join(tmp, "DTF Des-A.xlsx")
        b = os.path.join(tmp, "DTF Des-B.xlsx")
        missing = os.path.join(tmp, "gone.xlsx")
        Path(a).write_bytes(b"x")
        Path(b).write_bytes(b"x")

        gui = SimpleNamespace(input_file_paths=[a, b, missing], input_file_path=None)
        got = get_selected_input_files(gui)
        assert got == [a, b], got

        gui2 = SimpleNamespace(input_file_paths=[], input_file_path=a)
        assert get_selected_input_files(gui2) == [a]

        gui3 = SimpleNamespace(input_file_paths=[], input_file_path=None)
        assert get_selected_input_files(gui3) == []

    print("ok")


if __name__ == "__main__":
    main()
