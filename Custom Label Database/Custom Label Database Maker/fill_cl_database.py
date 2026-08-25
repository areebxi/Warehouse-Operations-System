import argparse
import csv
import io
import os
import re
import sys
from typing import Dict, List, Optional, Sequence


TOKEN_RE = re.compile(r"\{([^{}]+)\}")
# ProductExport cell values: keep ASCII letters, digits, and hyphens; other characters become spaces, then collapsed.
_SANITIZE_PRODUCT_VALUE = re.compile(r"[^a-zA-Z0-9-]+")
# Remove parenthetical / bracketed notes e.g. "Sport Grey (RS)" -> "Sport Grey " before sanitizing.
_PARENS_SEGMENT = re.compile(r"\([^()]*\)")
_BRACKETS_SEGMENT = re.compile(r"\[[^\[\]]*\]")
# Possessive apostrophe-s (Kid's -> Kids); other apostrophes are dropped (Das' -> Das).
_POSSESSIVE_APOSTROPHE_S = re.compile(r"'s\b", re.IGNORECASE)


def _normalize_apostrophes(value: str) -> str:
    """Kid's -> Kids; Das' Shirt -> Das Shirt (apostrophe removed, no extra space)."""
    value = _POSSESSIVE_APOSTROPHE_S.sub("s", value)
    return value.replace("'", "")


def _strip_bracketed_segments(value: str) -> str:
    """Remove (...) and [...] groups, innermost-first via repeated passes (handles simple nesting)."""
    s = value
    prev = None
    while prev != s:
        prev = s
        s = _BRACKETS_SEGMENT.sub("", s)
        s = _PARENS_SEGMENT.sub("", s)
    return s


def sanitize_product_field(value: str) -> str:
    """Strip bracketed segments, normalize apostrophes, then non-alphanumeric ASCII; collapse separators."""
    if not value:
        return ""
    value = _strip_bracketed_segments(value)
    value = _normalize_apostrophes(value)
    return _SANITIZE_PRODUCT_VALUE.sub(" ", value).strip()


def _read_csv_text(path: str, encoding: Optional[str]) -> tuple[str, str]:
    """Load file bytes and decode. If encoding is None, try utf-8-sig then cp1252 (typical Excel export on Windows)."""
    with open(path, "rb") as f:
        raw = f.read()
    if encoding is not None:
        return raw.decode(encoding), encoding
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1"), "latin-1"


def load_product_export(path: str, encoding: Optional[str]) -> tuple[List[str], List[Dict[str, str]]]:
    """Load ProductExport.csv into memory so we can expand multiple CL template rows."""
    text, _used_enc = _read_csv_text(path, encoding)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("ProductExport.csv has no header/fieldnames.")
    rows: List[Dict[str, str]] = []
    for row in reader:
        # csv.DictReader may return None values for missing columns; normalize to empty string
        rows.append({k: sanitize_product_field("" if v is None else v) for k, v in row.items()})
    return reader.fieldnames, rows


def cell_has_placeholders(cell: str) -> bool:
    return bool(TOKEN_RE.search(cell))


def replace_placeholders_in_cell(cell: str, product_row: Dict[str, str], source_name: str, row_num: int) -> str:
    """Replace {ColumnName} tokens using columns from ProductExport.csv.

    Product field values are already sanitized to ASCII letters, digits, and hyphens (see load_product_export).
    After substitution, any run of whitespace (including line breaks from the template layout)
    is collapsed to a single space so fields like Gender Apparel are one line.
    """

    def repl(match: re.Match) -> str:
        key = match.group(1)
        if key not in product_row:
            raise KeyError(
                f"Missing token column {key!r} referenced from CL {source_name} row {row_num}. "
                f"Available ProductExport columns do not include it."
            )
        return product_row[key]

    filled = TOKEN_RE.sub(repl, cell)
    return re.sub(r"\s+", " ", filled).strip()


def fill_cl_template(
    template_path: str,
    product_rows: Sequence[Dict[str, str]],
    out_path: str,
    read_encoding: Optional[str],
    write_encoding: str,
) -> None:
    # Read full template so encoding can be auto-detected; StringIO preserves embedded newlines in quoted fields.
    template_text, _used_enc = _read_csv_text(template_path, read_encoding)
    reader = csv.reader(io.StringIO(template_text))

    with open(out_path, "w", encoding=write_encoding, newline="") as f_out:
        writer = csv.writer(f_out)

        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("CL DatabaseX.csv appears to be empty (no header row).")

        writer.writerow(header)

        # Column indexes used for derived fields.
        # If CL headers change, we fail gracefully by skipping derived-field computation.
        try:
            gender_idx = header.index("Gender Apparel")
            colour_idx = header.index("Colour")
            apparel_idx = header.index("Apparel Image")
        except ValueError:
            gender_idx = colour_idx = apparel_idx = -1

        # CL row index is 1-based including header for clearer errors.
        cl_row_num = 1
        for row in reader:
            cl_row_num += 1

            # Template detection: a CL row is "template/placeholder" if any cell contains {..} tokens.
            # If it's a template row, replace it by N filled rows (N = number of ProductExport rows).
            if any(cell_has_placeholders(cell) for cell in row):
                for p_row in product_rows:
                    filled_row: List[str] = []
                    for cell in row:
                        if cell and cell_has_placeholders(cell):
                            filled_row.append(
                                replace_placeholders_in_cell(cell, p_row, "CL DatabaseX.csv", cl_row_num)
                            )
                        else:
                            filled_row.append(cell)

                    # Derived Apparel Image rule:
                    # If the template cell is the expression "(Gender Apparel)-(Colour Name)",
                    # compute it from the filled Gender Apparel and Colour values,
                    # converting spaces/newlines to dashes.
                    if apparel_idx >= 0 and apparel_idx < len(filled_row):
                        pic_cell = (filled_row[apparel_idx] or "").strip()
                        if re.fullmatch(r"\(Gender Apparel\)\s*-\s*\(Colour Name\)", pic_cell):
                            gender_val = filled_row[gender_idx] if 0 <= gender_idx < len(filled_row) else ""
                            colour_val = filled_row[colour_idx] if 0 <= colour_idx < len(filled_row) else ""

                            def to_dash(s: str) -> str:
                                s = (s or "").strip()
                                # Replace any whitespace runs (including embedded newlines) with '-'
                                # so values like "GILDAN\nSoftstyle Adult T-Shirt" become "GILDAN-Softstyle-Adult-T-Shirt".
                                s = re.sub(r"\s+", "-", s)
                                s = re.sub(r"-{2,}", "-", s)
                                return s

                            filled_row[apparel_idx] = f"{to_dash(gender_val)}-{to_dash(colour_val)}"

                    writer.writerow(filled_row)
            else:
                writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand CL DatabaseX.csv template rows using ProductExport.csv.")
    parser.add_argument(
        "--product",
        default=os.path.join(os.path.dirname(__file__), "ProductExport.csv"),
        help="Path to ProductExport.csv",
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

    _, product_rows = load_product_export(args.product, encoding=read_enc)
    fill_cl_template(args.template, product_rows, args.out, read_encoding=read_enc, write_encoding=write_enc)

    print(f"Wrote filled output to: {args.out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise

