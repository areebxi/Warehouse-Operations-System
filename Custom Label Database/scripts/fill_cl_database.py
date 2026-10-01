import argparse
import csv
import io
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

_WAREHOUSE = Path(__file__).resolve().parents[2]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
from scripts.fill_cl_database_impl import fill_cl_template, replace_placeholders_in_cell, _read_csv_text, load_btc_product_data, _strip_bracketed_segments, sanitize_product_field, _normalize_apostrophes, cell_has_placeholders


TOKEN_RE = re.compile(r"\{([^{}]+)\}")
# BTC Product Data cell values: keep ASCII letters, digits, and hyphens; other characters become spaces, then collapsed.
_SANITIZE_PRODUCT_VALUE = re.compile(r"[^a-zA-Z0-9-]+")
# Remove parenthetical / bracketed notes e.g. "Sport Grey (RS)" -> "Sport Grey " before sanitizing.
_PARENS_SEGMENT = re.compile(r"\([^()]*\)")
_BRACKETS_SEGMENT = re.compile(r"\[[^\[\]]*\]")
# Possessive apostrophe-s (Kid's -> Kids); other apostrophes are dropped (Das' -> Das).
_POSSESSIVE_APOSTROPHE_S = re.compile(r"'s\b", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand CL DatabaseX.csv template rows using BTC Product Data.")
    parser.add_argument(
        "--product",
        default=str(wh.btc_product_data_path()),
        help="Path to BTC_Product_Data.csv",
    )
    parser.add_argument(
        "--template",
        default=os.path.join(os.path.dirname(__file__), "CL DatabaseX.csv"),
        help="Path to CL DatabaseX.csv",
    )
    parser.add_argument(
        "--out",
        default=os.path.join(os.path.dirname(__file__), "CL DatabaseX_filled.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--encoding",
        default=None,
        metavar="ENC",
        help="Force input/output encoding. Default: detect each input (utf-8-sig then cp1252); output utf-8-sig.",
    )
    args = parser.parse_args()

    for p in [args.product, args.template]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found: {p}")

    read_enc: Optional[str] = args.encoding
    write_enc = args.encoding if args.encoding is not None else "utf-8-sig"

    _, product_rows = load_btc_product_data(args.product, encoding=read_enc)
    fill_cl_template(args.template, product_rows, args.out, read_encoding=read_enc, write_encoding=write_enc)

    print(f"Wrote filled output to: {args.out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise

