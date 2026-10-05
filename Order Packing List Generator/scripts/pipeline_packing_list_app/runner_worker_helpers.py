from __future__ import annotations

from pathlib import Path

from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner import run_pipeline
from pipeline_runtime.runner_utils import _sanitize_process_for_filename

from .config import DEFAULT_OUTPUT_DIR
from .runner_log import _make_pipeline_log_for_file
from .runner_validate import resolve_cl_csv_path


def make_run_with_log_file(app, *, logs_root: Path, ts: str, used_log_bases: set[str], open_files: list):
    def run_with_log_file(rel_stem: str, stdout_prefix: str) -> PipelineLog:
        safe = _sanitize_process_for_filename(rel_stem)
        base = f"{safe}_{ts}"
        name_base = base
        n = 2
        while name_base in used_log_bases:
            name_base = f"{base}_{n}"
            n += 1
        used_log_bases.add(name_base)
        log_path = (logs_root / f"{name_base}.log").resolve()
        pl, fp = _make_pipeline_log_for_file(app, log_file_path=log_path, stdout_prefix=stdout_prefix)
        open_files.append(fp)
        app._session_log_files.append(str(log_path))
        pl.detail(f"Full pipeline transcript (this run): {log_path}")
        return pl

    return run_with_log_file


def make_run_one_pipeline(app):
    def _logo_id_threshold() -> int:
        return (
            int(app.logo_id_threshold_var.get())
            if str(app.logo_id_threshold_var.get()).strip().isdigit()
            else 5
        )

    def _run_one_pipeline(
        csv_path: Path | str,
        *,
        pl: PipelineLog,
        use_fixed: bool,
        fixed_process: str | None,
        phases: str = "all",
    ):
        return run_pipeline(
            str(csv_path),
            app.date_var.get().strip(),
            app.shift_var.get().strip(),
            app.output_dir_var.get() or str(DEFAULT_OUTPUT_DIR),
            app.workbook_var.get(),
            app.apparel_dir_var.get() or None,
            app.logo_custom_single_dir_var.get() or None,
            app.logo_custom_double_dir_var.get() or None,
            app.logo_normal_dir_var.get() or None,
            separate_by_logo_id=app.separate_by_logo_id_var.get(),
            logo_id_threshold=_logo_id_threshold(),
            use_fixed_process_number=use_fixed,
            fixed_process_number=fixed_process,
            pdf_copy_dir=(app.pdf_copy_dir_var.get() or "").strip() or None,
            excel_copy_dir=(app.excel_copy_dir_var.get() or "").strip() or None,
            log=pl,
            phases=phases,  # type: ignore[arg-type]
            cl_csv_path=resolve_cl_csv_path(app),
            use_demo_images=app.use_demo_images_var.get(),
            make_design_queues=bool(app.make_design_queues_var.get()),
        )

    return _run_one_pipeline


def emit_batch_banner(app, message: str, logs: list[PipelineLog]) -> None:
    if app._log_queue is not None:
        app._log_queue.put(message)
    for _pl in logs:
        _pl.detail(message)
