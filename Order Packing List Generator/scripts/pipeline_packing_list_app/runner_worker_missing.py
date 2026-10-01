from __future__ import annotations

from pathlib import Path

from pipeline_runtime.runner import run_missing_logos_pipeline

from .config import DEFAULT_OUTPUT_DIR


def run_missing_logo_worker(app, *, ml_name: str, start_banner: str, run_with_log_file) -> None:
    inp = (app.input_csv_var.get() or "").strip()
    stem = Path(inp).stem if inp else "missing"
    pl = run_with_log_file(stem, "")
    pl.detail(start_banner)
    output_root = run_missing_logos_pipeline(
        app.input_csv_var.get().strip(),
        ml_name or "",
        app.output_dir_var.get() or str(DEFAULT_OUTPUT_DIR),
        app.date_var.get().strip(),
        app.apparel_dir_var.get() or None,
        app.logo_custom_single_dir_var.get() or None,
        app.logo_custom_double_dir_var.get() or None,
        app.logo_normal_dir_var.get() or None,
        shift=app.shift_var.get().strip(),
        pdf_copy_dir=(app.pdf_copy_dir_var.get() or "").strip() or None,
        excel_copy_dir=(app.excel_copy_dir_var.get() or "").strip() or None,
        log=pl,
        use_demo_images=app.use_demo_images_var.get(),
    )
    app.output_root, app.unmatched_path, app.missing_logo_path, app._pipeline_results = (
        output_root,
        None,
        None,
        None,
    )
