from __future__ import annotations

import base64
import io
from pathlib import Path

from PyPDF2 import PdfReader


def decode_label_pdf_bytes(label_data_b64: str) -> bytes:
    raw = base64.b64decode(label_data_b64.encode("ascii"), validate=False)
    # Validate it's a readable PDF (parity: "best effort validation").
    PdfReader(io.BytesIO(raw))
    return raw


def write_label_pdf(path: Path, *, label_data_b64: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = decode_label_pdf_bytes(label_data_b64)
    path.write_bytes(raw)

