"""Packing finishes PDFs before Design Queues; multi-file queues stay one-at-a-time."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.pipeline_packing_list_app.runner_worker_helpers import DesignQueueHandoff
from scripts.pipeline_runtime.runner_impl1 import run_pipeline


class _Var:
    def __init__(self, value) -> None:
        self.value = value

    def get(self):
        return self.value


def _ctx() -> dict:
    return {
        "input_csv_path": Path("in.csv"),
        "output_root": Path("out"),
        "token": "1",
        "workbook_path": Path("wb.xlsx"),
        "cl_csv": None,
        "shift_label": "1st Shift",
        "date_dd_mm_yyyy": "12-10-2026",
        "dispatch_date": None,
        "logo_custom_single_dir": None,
        "logo_custom_double_dir": None,
        "logo_normal_dir": None,
        "apparel_dir": None,
        "use_demo": False,
        "lc": lambda *_a, **_k: None,
    }


class TestAllPhaseOrder(unittest.TestCase):
    def test_all_phase_runs_excel_then_pdf_without_queues(self) -> None:
        ctx = _ctx()
        order: list[str] = []

        def excel(**_kwargs):
            order.append("excel")
            return ([], None, None)

        def pdf(**_kwargs):
            order.append("pdf")
            return (ctx["output_root"], None, None, None)

        with patch(
            "scripts.pipeline_runtime.runner_impl1.prepare_pipeline_run", return_value=ctx
        ), patch(
            "scripts.pipeline_runtime.runner_impl1.run_excel_steps", side_effect=excel
        ), patch(
            "scripts.pipeline_runtime.runner_impl1.finish_full_pipeline", side_effect=pdf
        ), patch(
            "scripts.pipeline_runtime.run_design_queues_step.run_design_queues_for_outputs"
        ) as queues:
            run_pipeline(
                input_csv="in.csv",
                date_dd_mm_yyyy="12-10-2026",
                shift="1st Shift",
                output_dir="out",
                workbook_path="wb.xlsx",
                apparel_dir=None,
                logo_custom_single_dir=None,
                logo_custom_double_dir=None,
                logo_normal_dir=None,
            )
        self.assertEqual(order, ["excel", "pdf"])
        queues.assert_not_called()


class TestDesignQueueHandoff(unittest.TestCase):
    def test_submits_run_one_at_a_time_in_order(self) -> None:
        app = type(
            "App",
            (),
            {
                "make_design_queues_var": _Var(True),
                "date_var": _Var("12-10-2026"),
                "shift_var": _Var("1st Shift"),
                "_log_queue": None,
            },
        )()
        seen: list[Path] = []

        def fake_run(roots, **_kwargs):
            seen.append(roots[0])
            return 0

        with patch(
            "scripts.pipeline_packing_list_app.runner_worker_helpers.run_design_queues_for_outputs",
            side_effect=fake_run,
        ):
            handoff = DesignQueueHandoff(app)
            handoff.submit(Path("a"), [])
            handoff.submit(Path("b"), [])
            handoff.finish()
        self.assertEqual(seen, [Path("a"), Path("b")])

    def test_off_skips_submit(self) -> None:
        app = type(
            "App",
            (),
            {
                "make_design_queues_var": _Var(False),
                "date_var": _Var("12-10-2026"),
                "shift_var": _Var("1st Shift"),
                "_log_queue": None,
            },
        )()
        with patch(
            "scripts.pipeline_packing_list_app.runner_worker_helpers.run_design_queues_for_outputs"
        ) as queues:
            handoff = DesignQueueHandoff(app)
            handoff.submit(Path("a"), [])
            handoff.finish()
        queues.assert_not_called()


if __name__ == "__main__":
    unittest.main()
