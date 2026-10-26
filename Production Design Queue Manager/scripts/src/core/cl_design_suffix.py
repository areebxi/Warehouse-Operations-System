"""Design-image suffix from a Custom Label row (letter only, no hyphen)."""

from __future__ import annotations

from typing import Optional

from shared import cl_columns as clc


def design_image_suffix(row, n: int) -> Optional[str]:
    """Return the filled suffix for position n, or None."""
    value = row.get(clc.design_image_suffix(n))
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text
