"""Self-check: Plain/Packs xlsx index cache hit + invalidate on mtime change."""

from __future__ import annotations

import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from openpyxl import Workbook

from catalog_cache import load_xlsx_index
from shared import paths as wh


def _write_xlsx(path: Path, sheet: str, headers: list[str], rows: list[list[str]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(headers)
    for row in rows:
        ws.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    wb.close()


def main() -> None:
    cache_dir = wh.sorter_catalog_cache_dir()
    stem = "_selfcheck_plain"
    cache_path = wh.sorter_catalog_cache_path(stem)
    xlsx = cache_dir / "_selfcheck_plain.xlsx"
    try:
        if cache_path.exists():
            cache_path.unlink()
        _write_xlsx(xlsx, "Sheet1", ["SKU", "Colour"], [["ABC-1", "Red"], ["DEF", "Blue"]])
        a = load_xlsx_index(xlsx, "Sheet1", "SKU", cache_stem=stem)
        assert a["abc-1"]["Colour"] == "Red"
        assert cache_path.is_file()
        mtime1 = cache_path.stat().st_mtime_ns
        b = load_xlsx_index(xlsx, "Sheet1", "SKU", cache_stem=stem)
        assert b == a
        assert cache_path.stat().st_mtime_ns == mtime1  # hit — cache file untouched
        time.sleep(0.05)
        _write_xlsx(xlsx, "Sheet1", ["SKU", "Colour"], [["ABC-1", "Green"]])
        c = load_xlsx_index(xlsx, "Sheet1", "SKU", cache_stem=stem)
        assert c["abc-1"]["Colour"] == "Green"
        assert cache_path.stat().st_mtime_ns != mtime1  # rebuilt
        print("catalog_cache ok")
    finally:
        for p in (cache_path, xlsx):
            if p.exists():
                p.unlink()


if __name__ == "__main__":
    main()
