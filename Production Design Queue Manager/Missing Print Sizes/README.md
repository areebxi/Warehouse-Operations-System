# Missing Print Sizes

When a design’s print size is missing from the Custom Label DB, Queue warns, exports those DTF Des rows here as Excel (`{source stem} ({timestamp}).xlsx`, or `DTF Des-Missing Print Sizes ({timestamp}).xlsx` with no source), and continues (image-dimension fallback where that already applies). Fix the CL print size, then re-run those rows.

Runtime exports are gitignored. Only this README is tracked.
