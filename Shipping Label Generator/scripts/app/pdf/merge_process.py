from __future__ import annotations

import io
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter


def merge_process_pdf(
    *,
    out_path: Path,
    summary_pdf_bytes: bytes,
    label_pdf_paths: list[Path],
    missed_pdf_bytes: bytes | None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    w = PdfWriter()
    w.append(PdfReader(io.BytesIO(summary_pdf_bytes)))
    for p in label_pdf_paths:
        w.append(PdfReader(p))
    if missed_pdf_bytes is not None:
        w.append(PdfReader(io.BytesIO(missed_pdf_bytes)))

    with out_path.open("wb") as f:
        w.write(f)

