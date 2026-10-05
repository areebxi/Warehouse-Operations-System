from __future__ import annotations

from pathlib import Path

from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.run_design_queues_step import run_design_queues_for_outputs
from pipeline_split_by_process_item.common import pin_batch_shift

from .runner_validate import get_input_paths
from .runner_worker_helpers import emit_batch_banner


def run_file_mode_pipelines(app, *, run_with_log_file, run_one_pipeline) -> tuple:
    pl: PipelineLog | None = None
    output_root = unmatched = missing_logo = None
    results: list[dict] = []

    paths = get_input_paths(app)
    # Sorter filename is the process name (PIN/PDF/Excel).
    use_fixed = True
    fixed_gui = (app.fixed_process_number_var.get() or "").strip()
    multi = len(paths) > 1
    batch_phase = "excel" if multi else "all"
    pdf_jobs = []

    def _skip_missing_csv(
        csv_path: Path,
        *,
        pl: PipelineLog,
        prefix: str,
        reason: str,
        phase: str,
    ) -> None:
        name = csv_path.stem
        line = f"Skipped {name} ({phase}): {reason}"
        pl.detail(line)
        if app._log_queue is not None:
            app._log_queue.put(f"{prefix}{line}")
        results.append(
            {
                "input": csv_path,
                "output_root": None,
                "unmatched": None,
                "missing_logo": None,
                "process_name": name,
                "missing_logos_report": None,
                "skipped": True,
                "skip_reason": reason,
            }
        )

    for csv_path in paths:
        prefix = f"[{pin_batch_shift(csv_path.stem)}] " if multi else ""
        pl = run_with_log_file(pin_batch_shift(csv_path.stem), prefix)
        # Sorter stem → B1-S1 for process, Output folder, missing-logo files.
        fixed_for_this = pin_batch_shift(
            csv_path.stem if multi else (fixed_gui or csv_path.stem)
        )
        start_msg = (
            "Starting Excel phase (batch)…"
            if multi
            else "Starting pipeline…"
        )
        pl.detail(start_msg)
        if app._log_queue is not None:
            app._log_queue.put(f"{prefix}{start_msg}")

        if multi and not Path(csv_path).exists():
            _skip_missing_csv(
                Path(csv_path),
                pl=pl,
                prefix=prefix,
                reason=f"Input CSV not found: {csv_path}",
                phase="Excel",
            )
            continue

        try:
            output_root, unmatched, missing_logo, missing_logos_report = (
                run_one_pipeline(
                    csv_path,
                    pl=pl,
                    use_fixed=use_fixed,
                    fixed_process=fixed_for_this,
                    phases=batch_phase,
                )
            )
        except FileNotFoundError as exc:
            if not multi:
                raise
            _skip_missing_csv(
                Path(csv_path),
                pl=pl,
                prefix=prefix,
                reason=str(exc),
                phase="Excel",
            )
            continue

        entry = {
            "input": csv_path,
            "output_root": output_root,
            "unmatched": unmatched,
            "missing_logo": missing_logo,
            "process_name": output_root.name if output_root else csv_path.stem,
            "missing_logos_report": missing_logos_report,
        }
        results.append(entry)
        if multi:
            pdf_jobs.append(
                {
                    "csv_path": csv_path,
                    "pl": pl,
                    "prefix": prefix,
                    "fixed_for_this": fixed_for_this,
                    "use_fixed": use_fixed,
                    "entry": entry,
                }
            )

    if multi and not pdf_jobs and any(r.get("skipped") for r in results):
        skipped_lines = [
            f"- {r.get('process_name')}: {r.get('skip_reason') or 'not found'}"
            for r in results
            if r.get("skipped")
        ]
        raise FileNotFoundError(
            "All input CSVs were skipped (not found / unavailable):\n"
            + "\n".join(skipped_lines)
        )

    if pdf_jobs:
        roots = [
            j["entry"]["output_root"]
            for j in pdf_jobs
            if j["entry"].get("output_root") is not None
        ]
        banner_q = (
            f"Batch: Excel complete for {len(pdf_jobs)} inputs — "
            "Design Queues step…"
        )
        emit_batch_banner(app, banner_q, [j["pl"] for j in pdf_jobs])
        run_design_queues_for_outputs(
            roots,
            make_design_queues=bool(app.make_design_queues_var.get()),
            log=(
                (lambda msg: emit_batch_banner(app, msg, [j["pl"] for j in pdf_jobs]))
                if pdf_jobs
                else None
            ),
            date_dd_mm_yyyy=app.date_var.get().strip(),
            shift_label=app.shift_var.get().strip(),
        )
        banner = (
            f"Batch: Design Queues done — starting PDF phase "
            f"for {len(pdf_jobs)} inputs…"
        )
        emit_batch_banner(app, banner, [j["pl"] for j in pdf_jobs])
        for job in pdf_jobs:
            job["pl"].detail(f"{job['prefix']}Starting PDF phase…")
            if app._log_queue is not None:
                app._log_queue.put(f"{job['prefix']}Starting PDF phase…")
            try:
                _, _, _, missing_logos_report = run_one_pipeline(
                    job["csv_path"],
                    pl=job["pl"],
                    use_fixed=job["use_fixed"],
                    fixed_process=job["fixed_for_this"],
                    phases="pdf",
                )
            except FileNotFoundError as exc:
                reason = str(exc)
                line = (
                    f"Skipped {Path(job['csv_path']).stem} (PDF): {reason}"
                )
                job["pl"].detail(line)
                if app._log_queue is not None:
                    app._log_queue.put(f"{job['prefix']}{line}")
                job["entry"]["pdf_skipped"] = True
                job["entry"]["pdf_skip_reason"] = reason
                continue
            job["entry"]["missing_logos_report"] = missing_logos_report
            output_root = job["entry"]["output_root"]
            unmatched = job["entry"]["unmatched"]
            missing_logo = job["entry"]["missing_logo"]
    return output_root, unmatched, missing_logo, results
