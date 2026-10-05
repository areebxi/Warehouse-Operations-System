"""Copy saved queue PNGs into the configured DTF Queues folder."""

from __future__ import annotations

import os
import shutil
from typing import List, Optional, Tuple


def copy_pngs_to_dtf_queues(
    png_paths: List[str],
    dtf_queues_folder: Optional[str],
) -> Tuple[bool, str]:
    """Copy PNG files into the DTF Queues folder. Overwrites same-named files."""
    if not dtf_queues_folder:
        return False, "DTF Queues folder not configured"

    if not os.path.isdir(dtf_queues_folder):
        return False, f"DTF Queues folder does not exist: {dtf_queues_folder}"

    if not png_paths:
        return False, "No PNG files to copy"

    copied: List[str] = []
    for png_path in png_paths:
        if not os.path.isfile(png_path):
            return False, f"PNG file does not exist: {png_path}"
        try:
            dest = os.path.join(dtf_queues_folder, os.path.basename(png_path))
            shutil.copy2(png_path, dest)
            copied.append(os.path.basename(png_path))
        except Exception as e:
            return False, f"Error copying {os.path.basename(png_path)}: {e}"

    return True, f"Copied {len(copied)} PNG(s):\n" + "\n".join(copied[:20]) + (
        "\n..." if len(copied) > 20 else ""
    )


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "src")
        dest = os.path.join(tmp, "queues")
        os.makedirs(src)
        os.makedirs(dest)
        a = os.path.join(src, "A.png")
        b = os.path.join(src, "B.png")
        open(a, "wb").write(b"a")
        open(b, "wb").write(b"b")
        ok, msg = copy_pngs_to_dtf_queues([a, b], dest)
        assert ok, msg
        assert os.path.isfile(os.path.join(dest, "A.png"))
        assert os.path.isfile(os.path.join(dest, "B.png"))
        ok2, _ = copy_pngs_to_dtf_queues([a], None)
        assert not ok2
        print("dtf_queues_copy self-check OK")
