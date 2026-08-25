# Queue App — Issue Resolution Log

Newest entries first. Maintained automatically per `.cursor/rules/issue-resolution-log.mdc`.

---

### 2026-08-09 09:41 UTC+1
**Issue:** Size lookup still had legacy J=9/K=10 column-index fallback after the Front Print crash fix.
**Resolution:** Removed `_try_column_index_fallback` and `_row_value_at` from `size_reference.py`; width/height now use named columns only (`Size Width`, `Size Height`, etc.) in `get_size_from_reference` and `multi_position_logic.py`.

### 2026-08-09 09:40 UTC+1
**Issue:** Arrange designs failed with `could not convert string to float: 'Front Print'` (e.g. on `DTF Des-P100.xlsx` / `M96 (17257)`).
**Resolution:** In `scripts/src/core/size_reference.py` `_try_column_index_fallback`, skip obsolete J=9/K=10 fallback when named dim columns exist (index 9 is now `Printing Position`); also guard legacy `float()` against non-numeric cells.

### 2026-08-04 12:27 UTC+1
**Issue:** No standing process to record issues discussed with the agent and how they were fixed.
**Resolution:** Added always-apply rule `.cursor/rules/issue-resolution-log.mdc` and this log file (`.cursor/issue-log.md`). Future issue discussions are appended here with date/time, issue, and resolution.
