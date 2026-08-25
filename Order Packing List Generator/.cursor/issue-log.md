# Issue Log

Issues discussed with the AI agent, newest first.

<!-- Entries are appended below this line -->

## 2026-08-09 10:38

**Issue:** Packing List process field label said "Fixed process number" instead of matching Preflight's "Process number".

**Resolution:** Renamed the label to "Process number:" in `scripts/pipeline_packing_list_app/ui.py`.

## 2026-08-07 05:45

**Issue:** Packing List GUI field order differed from Preflight; fixed process number was near the bottom instead of below Shift.

**Resolution:** Reordered fields in `scripts/pipeline_packing_list_app/ui.py` to match Preflight (Date → Shift → fixed process → Input CSV → Workbook → Output → folders), keeping Packing-only options after the shared path block.
