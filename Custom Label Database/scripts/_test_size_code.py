"""Quick checks for size_code_logic worked examples."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from size_code_logic import (
    extract_size_code,
    load_overrides,
    load_size_ref_index,
    resolve_print_dims,
    resolve_sr_rows,
)

CONFIG = Path(__file__).resolve().parents[1] / "Configuration Workbook.xlsx"


def main() -> None:
    index = load_size_ref_index(CONFIG)
    overrides = load_overrides(CONFIG)
    cases = [
        ("121913LG-K-SS-LPNK-YXS", "K-SS|YXS"),
        ("128968LG-W115-BLK-S-Yes", "W115|S"),
        ("88892LG-K-T-LPNK-YS", "K-T|-YS"),  # leading-dash form as stored
        ("121122LG-K-H-DHR-YL", "K-H"),
        ("77989LG-M-T-BLK-L", "M-T|-L"),
        ("2400-M-T-BLK-L", "M-T|-L"),
        ("K-SS-WHI-YS", None),  # may be K-SS only — no (YS) in our sheet
        ("24LBL-A4-STCKR-45mm", "A4"),
        ("BZ02-T-T-LBL-2-3Yrs", "BZ02"),
        ("10AILG-M-T-WHI-L", "10AILG-M-T"),  # longer bare beats M-T|-L
    ]
    print("bases", len(index.bases_longest_first))
    for sku, expect in cases:
        code, ov = extract_size_code(sku, index, overrides)
        rows = resolve_sr_rows(code, index) if code else []
        wh = [(r.w, r.h, r.n_designs, r.suffix) for r in rows[:4]]
        mark = "OK" if (expect is None or code == expect or (expect and code and code.replace("|-", "|") == expect.replace("|-", "|"))) else "??"
        # softer: allow K-T|YS vs K-T|-YS
        if expect and code:
            eb, ebr = (expect.split("|", 1) + [None])[:2] if "|" in expect else (expect, None)
            cb, cbr = (code.split("|", 1) + [None])[:2] if "|" in code else (code, None)
            if eb == cb and (
                ebr == cbr
                or (ebr and cbr and ebr.lstrip("-") == cbr.lstrip("-"))
            ):
                mark = "OK"
            elif expect == code:
                mark = "OK"
            else:
                mark = "??"
        print(f"{mark} {sku}")
        print(f"   got={code!r} expect~{expect!r} ov={ov.contain if ov else None} rows={wh}")

    # dims sample
    r = resolve_print_dims("121913LG-K-SS-LPNK-YXS", "Front Center", index, overrides)
    print("\nresolve K-SS|YXS", r)


if __name__ == "__main__":
    main()
