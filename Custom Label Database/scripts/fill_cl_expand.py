"""Expand CL template rows from BTC Product Data."""
from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, Optional, Sequence

from fill_cl_sanitize import (
    _read_csv_text,
    cell_has_placeholders,
    replace_placeholders_in_cell,
)


def fill_cl_template(
    template_path: str,
    product_rows: Sequence[Dict[str, str]],
    out_path: str,
    read_encoding: Optional[str],
    write_encoding: str,
) -> None:
    template_text, _used_enc = _read_csv_text(template_path, read_encoding)
    reader = csv.reader(io.StringIO(template_text))

    with open(out_path, "w", encoding=write_encoding, newline="") as f_out:
        writer = csv.writer(f_out)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CL DatabaseX.csv appears to be empty (no header row).")
        writer.writerow(header)

        try:
            gender_idx = header.index("Gender Apparel")
            colour_idx = header.index("Colour")
            apparel_idx = header.index("Apparel Image")
        except ValueError:
            gender_idx = colour_idx = apparel_idx = -1

        cl_row_num = 1
        for row in reader:
            cl_row_num += 1
            if any(cell_has_placeholders(cell) for cell in row):
                for p_row in product_rows:
                    filled_row: List[str] = []
                    for cell in row:
                        if cell and cell_has_placeholders(cell):
                            filled_row.append(
                                replace_placeholders_in_cell(
                                    cell, p_row, "CL DatabaseX.csv", cl_row_num
                                )
                            )
                        else:
                            filled_row.append(cell)

                    if apparel_idx >= 0 and apparel_idx < len(filled_row):
                        pic_cell = (filled_row[apparel_idx] or "").strip()
                        if re.fullmatch(r"\(Gender Apparel\)\s*-\s*\(Colour Name\)", pic_cell):
                            gender_val = (
                                filled_row[gender_idx] if 0 <= gender_idx < len(filled_row) else ""
                            )
                            colour_val = (
                                filled_row[colour_idx] if 0 <= colour_idx < len(filled_row) else ""
                            )

                            def to_dash(s: str) -> str:
                                s = (s or "").strip()
                                s = re.sub(r"\s+", "-", s)
                                s = re.sub(r"-{2,}", "-", s)
                                return s

                            filled_row[apparel_idx] = f"{to_dash(gender_val)}-{to_dash(colour_val)}"
                    writer.writerow(filled_row)
            else:
                writer.writerow(row)
