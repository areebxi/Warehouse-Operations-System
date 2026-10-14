from __future__ import annotations

from pathlib import Path

from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_split_by_process_item.common import pin_batch_shift

from .runner_validate import get_input_paths
from .runner_worker_helpers import DesignQueueHandoff, handoff_design_queues


def run_file_mode_pipelines(app, *, run_with_log_file, run_one_pipeline) -> tuple:
    pl: PipelineLog | None = None
    output_root = unmatched = missing_logo = None
    results: list[dict] = []

    paths = get_input_paths(app)
    # Sorter filename is the process name (PIN/PDF/Excel).
    use_fixed = True
    fixed_gui = (app.fixed_process_number_var.get() or "").strip()
    multi = len(paths) > 1
    handoff = DesignQueueHandoff(app) if multi else None
    ran_any = False

    def _skip_missing_csv(
        csv_path: Path,
        *,
        pl: PipelineLog,
        prefix: str,
        reason: str,
    ) -> None:
        name = csv_path.stem
        line = f"Skipped {name}: {reason}"
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

    try:
        for csv_path in paths:
            prefix = f"[{pin_batch_shift(csv_path.stem)}] " if multi else ""
            pl = run_with_log_file(pin_batch_shift(csv_path.stem), prefix)
            # Sorter stem → B1-S1 for process, Output folder, missing-logo files.
            fixed_for_this = pin_batch_shift(
                csv_path.stem if multi else (fixed_gui or csv_path.stem)
            )
            start_msg = "Starting pipeline…"
            pl.detail(start_msg)
            if app._log_queue is not None:
                app._log_queue.put(f"{prefix}{start_msg}")

            if multi and not Path(csv_path).exists():
                _skip_missing_csv(
                    Path(csv_path),
                    pl=pl,
                    prefix=prefix,
                    reason=f"Input CSV not found: {csv_path}",
                )
                continue

            try:
                output_root, unmatched, missing_logo, missing_logos_report = (
                    run_one_pipeline(
                        csv_path,
                        pl=pl,
                        use_fixed=use_fixed,
                        fixed_process=fixed_for_this,
                        phases="all",
                    )
                )
            except FileNotFoundError as exc:
                if not multi:
                    raise
                _skip_missing_csv(
                    Path(csv_path), pl=pl, prefix=prefix, reason=str(exc)
                )
                continue

            ran_any = True
            results.append(
                {
                    "input": csv_path,
                    "output_root": output_root,
                    "unmatched": unmatched,
                    "missing_logo": missing_logo,
                    "process_name": output_root.name if output_root else csv_path.stem,
                    "missing_logos_report": missing_logos_report,
                }
            )
            if handoff is not None:
                handoff.submit(output_root, [pl])
            else:
                handoff_design_queues(app, output_root, [pl])

        if multi and not ran_any and any(r.get("skipped") for r in results):
            skipped_lines = [
                f"- {r.get('process_name')}: {r.get('skip_reason') or 'not found'}"
                for r in results
                if r.get("skipped")
            ]
            raise FileNotFoundError(
                "All input CSVs were skipped (not found / unavailable):\n"
                + "\n".join(skipped_lines)
            )
    finally:
        if handoff is not None:
            handoff.finish()
    return output_root, unmatched, missing_logo, results
