from __future__ import annotations

from pathlib import Path

from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.read_group import GroupedOrders, OrderInput
from scripts.app.flows.print_labels.run import (
    _manual_job_has_outputs,
    _manual_job_id_from_groups,
    _manual_job_paths,
)


def _cfg(tmp_path: Path) -> AppConfig:
    return AppConfig(
        raw={
            "paths": {
                "output_dir": str(tmp_path / "output"),
                "logs_dir": str(tmp_path / "logs"),
            },
            "manual_print": {
                "input_csv": str(tmp_path / "Manual Print Input" / "Order Numbers.csv"),
            },
        },
        provider_name="real",
    )


def test_manual_job_id_from_groups_joins_sorted_process_numbers() -> None:
    groups = [
        GroupedOrders("2450", [OrderInput("o1")]),
        GroupedOrders("2000", [OrderInput("o2"), OrderInput("o3")]),
        GroupedOrders("2400", [OrderInput("o4")]),
    ]
    assert _manual_job_id_from_groups(groups) == "2000-2400-2450"


def test_manual_job_id_from_groups_single_process() -> None:
    groups = [GroupedOrders("2000", [OrderInput("o1")])]
    assert _manual_job_id_from_groups(groups) == "2000"


def test_manual_job_has_outputs_detects_existing_combined_pdf(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    job_id = "2000-2400-2450"
    existing = tmp_path / "output" / "Manual Outputs" / "Combined_PDFs" / "2099-01-01" / f"{job_id}.pdf"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"%PDF")

    assert _manual_job_has_outputs(cfg=cfg, date_dir="2099-01-01", job_id=job_id) is True


def test_manual_job_paths_use_manual_output_and_log_roots(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    job_id = "2000-2400-2450"
    paths = _manual_job_paths(
        cfg=cfg,
        date_dir="2099-01-01",
        job_id=job_id,
        process_numbers={"2000", "2400", "2450"},
    )

    assert paths["combined_pdf"] == tmp_path / "output" / "Manual Outputs" / "Combined_PDFs" / "2099-01-01" / f"{job_id}.pdf"
    assert paths["process_pdfs_dir"] == tmp_path / "output" / "Manual Outputs" / "Process_PDFs" / "2099-01-01" / "Manual" / job_id
    assert paths["labels_process_2000"] == tmp_path / "output" / "Manual Outputs" / "Labels" / "2099-01-01" / "process_2000"
    assert paths["labels_process_2400"] == tmp_path / "output" / "Manual Outputs" / "Labels" / "2099-01-01" / "process_2400"
    assert paths["logs_dir"] == tmp_path / "logs" / "Manual Print Logs" / "2099-01-01" / job_id
