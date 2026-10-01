"""
Phase 5 — Fill print Width/Height (mm) and Position 1-4 Name.

Supervisor choices (17 Aug 2026):
  Blank Print Positions -> Front Center
  Pocket -> always 80 x 100
  Front and Back -> same mm
  Print Sizes.xlsx first (shirts); Size References for bags/other
  Printing Size A3/A4 picks Print Sizes column; missing -> A4
  DB Size first; PE Size via Custom Label UID if unmapped
  Women -> Men size band
  Number of Designs drives extra slots
  Extra slots: Position names + W/H; Print Positions cell unchanged (except blanks)
  Sleeve / corners / kebab -> leave W/H blank
  No overwrite of existing mm
"""
from __future__ import annotations

import shutil
from datetime import datetime

import pandas as pd

from phase5_loaders import load_pe_sizes, load_print_sizes, load_size_ref
from phase5_maps import BACKUP, LOG, OUT, SRC
from phase5_process import process_rows


def _write_changelog(counts: dict, samples: list, rows_n: int) -> None:
    sample_txt = pd.DataFrame(samples).to_string(index=False) if samples else "(none)"
    log = f"""# Phase 5 Changelog — Print sizes

**Executed:** {datetime.now().strftime('%d %B %Y')}  
**Supervisor approval:** implement print Width/Height + Position names (choice A)

**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `{BACKUP.name}`  
**Rows:** {rows_n:,} (unchanged — no deletes)

---

## Rules applied

- Blank Print Positions -> `Front Center`
- Pocket -> 80 x 100 mm
- Front and Back -> same millimetres
- Print Sizes.xlsx first (shirts); Size References for bags / unmapped sizes
- Printing Size A3/A4 selects the Print Sizes column; missing -> A4
- Database Size first; ProductExport Size via Custom Label UID if unmapped
- Women uses Men Print Sizes band
- Number of Designs adds extra Position name + W/H slots; Print Positions text not expanded
- Sleeve / corners / kebab-case: Position name may be set; Width/Height left blank
- Overwrite Width/Height for bracket-matched mock+inside cases when Size References disagree

---

## Summary

| Metric | Count |
|--------|------:|
| Blank Print Positions set to Front Center | {counts.get('blank_pp_set_front_center', 0):,} |
| Print Positions now filled | {counts.get('pp_filled', 0):,} |
| Size References matched | {counts.get('size_ref_matched', 0):,} |
| Size References unmatched | {counts.get('size_ref_unmatched', 0):,} |
| Rows using Print Sizes.xlsx | {counts.get('used_print_sizes', 0):,} |
| Rows using PE Size fallback | {counts.get('used_pe_size', 0):,} |
| Extra position names from Size References | {counts.get('extra_position_from_sr', 0):,} |
| Rows with at least one W/H filled | {counts.get('rows_with_wh', 0):,} |
| Rows with no W/H | {counts.get('rows_no_wh', 0):,} |
| Position 1 Name filled | {counts.get('pos1_filled', 0):,} |
| Width 1 (mm) filled | {counts.get('width1_filled', 0):,} |
| Height 1 (mm) filled | {counts.get('height1_filled', 0):,} |
| Width 1 cells written | {counts.get('filled_Width 1 (mm)', 0):,} |
| Width 2 cells written | {counts.get('filled_Width 2 (mm)', 0):,} |
| Width 3 cells written | {counts.get('filled_Width 3 (mm)', 0):,} |
| Width 4 cells written | {counts.get('filled_Width 4 (mm)', 0):,} |
| W/H from pocket fixed 80x100 | {counts.get('wh_from_pocket_fixed', 0):,} |
| W/H from Print Sizes.xlsx | {counts.get('wh_from_print_sizes', 0):,} |
| W/H from Size References | {counts.get('wh_from_size_ref', 0) + counts.get('wh_from_size_ref_front_for_back', 0) + counts.get('wh_from_size_ref_any', 0):,} |
| Other positions skipped (no mm) | {counts.get('skipped_other_position', 0):,} |

---

## Sample filled rows

```
{sample_txt}
```

---

*See: [PHASE_5_PRINT_SIZES_PLAN.md](PHASE_5_PRINT_SIZES_PLAN.md)*
"""
    LOG.write_text(log, encoding="utf-8")


def main() -> None:
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading Print Sizes...", flush=True)
    ps_table = load_print_sizes()
    print(f"  {len(ps_table)} apparel size bands", flush=True)

    print("Loading Size References...", flush=True)
    mock_blocks, mock_inside_blocks, sku_index, pc_index = load_size_ref()
    print(
        f"  mock blocks={len(mock_blocks)} sku keys={len(sku_index)} pc keys={len(pc_index)}",
        flush=True,
    )

    print("Loading PE sizes...", flush=True)
    pe_sizes = load_pe_sizes()
    print(f"  {len(pe_sizes)} UIDs", flush=True)

    print("Loading CLD...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

    counts, samples, meta = process_rows(
        df, ps_table, mock_blocks, mock_inside_blocks, sku_index, pc_index, pe_sizes
    )

    print("Counts:", dict(counts), flush=True)
    if samples:
        print(pd.DataFrame(samples).to_string(index=False), flush=True)

    print(f"Writing {OUT} ...", flush=True)
    df.to_excel(OUT, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

    _write_changelog(counts, samples, meta["rows_n"])
    print(f"Changelog: {LOG}", flush=True)
    print("Phase 5 print sizes complete.", flush=True)


def _selfcheck() -> None:
    from phase5_helpers import classify, map_sr_size, paper_from_printing_size
    from phase5_lookup import normalize_gender_apparel_for_sr_sku

    assert classify("Front Center") == "front"
    assert classify("Front Left Pocket") == "pocket"
    assert map_sr_size("S") == "Small"
    assert paper_from_printing_size("") == "A4"
    assert normalize_gender_apparel_for_sr_sku("C800T-BS") == ["C800T"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h", "--selfcheck"):
        if sys.argv[1] == "--selfcheck":
            _selfcheck()
            print("phase5_print_sizes selfcheck OK")
        else:
            print(__doc__)
            print("Usage: python phase5_print_sizes.py [--selfcheck]")
        raise SystemExit(0)
    main()
