from __future__ import annotations

from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_shipstation.client import ShipStationError
from pipeline_shipstation.orders_to_csv import fetch_tag_orders_to_csv
from pipeline_shipstation.sync_tags_xlsx import DEFAULT_XLSX_PATH
from pipeline_shipstation.tags_process_lookup import resolve_tag_list_processes

from .config import PROJECT_ROOT
from .runner_worker_helpers import emit_batch_banner


def run_tag_mode_pipelines(app, *, run_with_log_file, run_one_pipeline) -> tuple:
    pl: PipelineLog | None = None
    output_root = unmatched = missing_logo = None
    results: list[dict] = []

    tags = (
        app.selected_shipstation_tags()
        if hasattr(app, "selected_shipstation_tags")
        else (
            [app.selected_shipstation_tag()]
            if app.selected_shipstation_tag()
            else []
        )
    )
    tags = [t for t in tags if t]
    if not tags:
        raise ShipStationError("No ShipStation tag selected.")
    multi_tags = len(tags) > 1
    gui_value = (
        ""
        if multi_tags
        else (app.fixed_process_number_var.get() or "").strip()
    )
    resolved, err = resolve_tag_list_processes(
        tags,
        shift_label=app.shift_var.get().strip(),
        gui_value=gui_value,
    )
    if err or not resolved:
        raise ShipStationError(err or "Could not resolve process numbers.")
    if len(resolved) == 1 and not gui_value:
        app.root.after(0, app.fixed_process_number_var.set, resolved[0][2])

    batch_phase = "excel" if multi_tags else "all"
    pdf_jobs: list[dict] = []

    for tag_id, tag_name, process_name in resolved:
        prefix = f"[{process_name}] " if multi_tags else ""
        pl = run_with_log_file(process_name or tag_name or "shipstation", prefix)

        def _fetch_log(msg: str, _pl=pl) -> None:
            _pl.detail(msg)
            if app._log_queue is not None:
                app._log_queue.put(msg)

        if multi_tags or not gui_value:
            pl.detail(
                f"Using process {process_name} from {DEFAULT_XLSX_PATH.name} "
                f"for tag '{tag_name}' / shift '{app.shift_var.get().strip()}'."
            )
        csv_path = fetch_tag_orders_to_csv(
            tag_id=tag_id,
            tag_name=tag_name,
            date_dd_mm_yyyy=app.date_var.get().strip(),
            shift_label=app.shift_var.get().strip(),
            process_number=process_name,
            input_root=PROJECT_ROOT / "Input",
            log=_fetch_log,
        )
        start_msg = (
            "Starting Excel phase (batch)…"
            if multi_tags
            else "Starting pipeline…"
        )
        pl.detail(start_msg)
        if app._log_queue is not None:
            app._log_queue.put(f"{prefix}{start_msg}")
        output_root, unmatched, missing_logo, missing_logos_report = run_one_pipeline(
            csv_path,
            pl=pl,
            use_fixed=True,
            fixed_process=process_name,
            phases=batch_phase,
        )
        entry = {
            "input": csv_path,
            "output_root": output_root,
            "unmatched": unmatched,
            "missing_logo": missing_logo,
            "process_name": output_root.name if output_root else process_name,
            "missing_logos_report": missing_logos_report,
        }
        results.append(entry)
        if multi_tags:
            pdf_jobs.append(
                {
                    "csv_path": csv_path,
                    "pl": pl,
                    "prefix": prefix,
                    "process_name": process_name,
                    "entry": entry,
                }
            )

    if pdf_jobs:
        banner = (
            f"Batch: Excel complete for {len(pdf_jobs)} inputs — starting PDF phase…"
        )
        emit_batch_banner(app, banner, [j["pl"] for j in pdf_jobs])
        for job in pdf_jobs:
            job["pl"].detail(f"{job['prefix']}Starting PDF phase…")
            if app._log_queue is not None:
                app._log_queue.put(f"{job['prefix']}Starting PDF phase…")
            _, _, _, missing_logos_report = run_one_pipeline(
                job["csv_path"],
                pl=job["pl"],
                use_fixed=True,
                fixed_process=job["process_name"],
                phases="pdf",
            )
            job["entry"]["missing_logos_report"] = missing_logos_report
            output_root = job["entry"]["output_root"]
            unmatched = job["entry"]["unmatched"]
            missing_logo = job["entry"]["missing_logo"]
    return output_root, unmatched, missing_logo, results
