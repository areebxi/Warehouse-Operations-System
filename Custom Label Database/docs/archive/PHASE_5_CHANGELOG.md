# Phase 5 Changelog — Print sizes

**Executed:** 19 August 2026  
**Supervisor approval:** implement print Width/Height + Position names (choice A)

**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `Custom Label Database_Updated_prePhase5Print_20260819_163628.xlsx`  
**Rows:** 65,560 (unchanged — no deletes)

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
| Blank Print Positions set to Front Center | 0 |
| Print Positions now filled | 65,560 |
| Size References matched | 45,468 |
| Size References unmatched | 20,092 |
| Rows using Print Sizes.xlsx | 61,283 |
| Rows using PE Size fallback | 1,616 |
| Extra position names from Size References | 0 |
| Rows with at least one W/H filled | 64,601 |
| Rows with no W/H | 959 |
| Position 1 Name filled | 65,560 |
| Width 1 (mm) filled | 64,601 |
| Height 1 (mm) filled | 64,601 |
| Width 1 cells written | 5,364 |
| Width 2 cells written | 3,021 |
| Width 3 cells written | 0 |
| Width 4 cells written | 0 |
| W/H from pocket fixed 80x100 | 9,768 |
| W/H from Print Sizes.xlsx | 40,402 |
| W/H from Size References | 1,876 |
| Other positions skipped (no mm) | 1,004 |

---

## Sample filled rows

```
                Custom Label        Size           PP           P1  W1  H1 P2 W2 H2         src
    F8-M-PS-UCC003-WHI-M-YES      Medium Front Center Front Center 267 378          print_sizes
    F8-M-PS-UCC003-WHE-L-Yes       Large Front Center Front Center 267 378          print_sizes
   F8-M-PS-UCC003-WHE-XL-Yes Extra Large Front Center Front Center 267 378          print_sizes
  F8-M-PS-UCC003-WHE-2XL-Yes         2XL Front Center Front Center 267 378          print_sizes
       M-PS-UCC003-BOTGN-4XL         4XL Front Center Front Center 318 450          print_sizes
F8-M-PS-UCC003-BOTGN-4XL-Yes         4XL Front Center Front Center 318 450          print_sizes
  F8-M-PS-UCC003-NAVBE-S-Yes       Small Front Center Front Center 237 336          print_sizes
  F8-M-PS-UCC003-NAVBE-M-Yes      Medium Front Center Front Center 267 378          print_sizes
```

---

*See: [PHASE_5_PRINT_SIZES_PLAN.md](PHASE_5_PRINT_SIZES_PLAN.md)*
