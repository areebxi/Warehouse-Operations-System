"""ponytail: Areeb maps — fails if BTC/Uneek/CL standard joins drift."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test_fill_areeb_taxonomy_cases import assert_cl_cases, catalogs
from test_fill_areeb_taxonomy_plain import assert_plain_cases


def main() -> None:
    cat = catalogs()
    assert_plain_cases(cat)
    assert_cl_cases(cat)
    print("areeb taxonomy ok")


if __name__ == "__main__":
    main()
