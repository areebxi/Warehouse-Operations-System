from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Discovery:
    mode: str  # "csv" | "excel"
    files: list[Path]


def discover_input_files(desfiles_dir: Path) -> Discovery:
    desfiles_dir.mkdir(parents=True, exist_ok=True)

    csvs = sorted([p for p in desfiles_dir.glob("*.csv") if p.is_file()])
    if csvs:
        return Discovery(mode="csv", files=csvs)

    excels: list[Path] = []
    for ext in ("*.xlsx", "*.xls", "*.xlsm"):
        excels.extend([p for p in desfiles_dir.glob(ext) if p.is_file()])
    excels = sorted(excels)
    if excels:
        return Discovery(mode="excel", files=excels)

    raise FileNotFoundError(f"no files found in {desfiles_dir}")

