"""Tests for run_pipeline excel/pdf phases and step-6 CSV discovery."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts.pipeline_runtime.runner import discover_step6_csvs, run_pipeline


class TestDiscoverStep6Csvs(unittest.TestCase):
    def test_excludes_intermediates_keeps_process_csvs(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = "100"
            (root / f"1_fetch_input_csv_{token}.csv").write_text("a\n", encoding="utf-8")
            (root / f"5_assign_process_number_{token}.csv").write_text("a\n", encoding="utf-8")
            (root / f"missing_logo_orders_{token}.csv").write_text("a\n", encoding="utf-8")
            (root / "_scratch.csv").write_text("a\n", encoding="utf-8")
            keep = root / "100ANND1X.csv"
            keep.write_text("a\n", encoding="utf-8")
            found = discover_step6_csvs(root, token)
            self.assertEqual(found, [keep])


class TestPipelinePhases(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.input_csv = self.root / "3500.csv"
        self.input_csv.write_text("Order Number\n1\n", encoding="utf-8")
        self.output_dir = self.root / "Output"
        self.workbook = self.root / "Workbook.xlsx"
        self.workbook.write_bytes(b"PK")  # placeholder; not opened in pdf-only mocked path

    def _common_kwargs(self):
        return dict(
            input_csv=self.input_csv,
            date_dd_mm_yyyy="30-07-2026",
            shift="AM",
            output_dir=self.output_dir,
            workbook_path=self.workbook,
            apparel_dir=None,
            logo_custom_single_dir=None,
            logo_custom_double_dir=None,
            logo_normal_dir=None,
            log=None,
        )

    def test_invalid_phases(self) -> None:
        with self.assertRaises(ValueError):
            run_pipeline(**self._common_kwargs(), phases="nope")  # type: ignore[arg-type]

    def test_pdf_phase_requires_existing_output(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_pipeline(**self._common_kwargs(), phases="pdf")

    def test_pdf_phase_calls_step8_only(self) -> None:
        out_root = self.output_dir / "30-07-2026" / "AM Shift" / "3500"
        out_root.mkdir(parents=True)
        proc = out_root / "3500ANND1X.csv"
        proc.write_text("Order Number\n1\n", encoding="utf-8")

        with patch(
            "scripts.pipeline_runtime.runner.run_step8_pdf_generation_impl",
            return_value="ok",
        ) as mock_s8, patch(
            "scripts.pipeline_runtime.runner.fetch_input_csv"
        ) as mock_fetch:
            output_root, unmatched, missing, report = run_pipeline(
                **self._common_kwargs(), phases="pdf"
            )
        mock_fetch.assert_not_called()
        mock_s8.assert_called_once()
        self.assertEqual(output_root, out_root)
        self.assertIsNone(unmatched)
        self.assertIsNone(missing)
        self.assertEqual(report, "ok")
        self.assertEqual(mock_s8.call_args.kwargs["step6_csvs"], [proc])

    def test_excel_phase_skips_step8(self) -> None:
        """Run excel phase with steps stubbed; Step 8 must not run."""
        step6_name = "3500ANND1X.csv"

        def fake_fetch(_path):
            return [{"Order Number": "1"}]

        def fake_write(_rows, path):
            Path(path).write_text("Order Number\n1\n", encoding="utf-8")

        def fake_enrich(_path, _wb, log=None):
            import pandas as pd

            return pd.DataFrame([{"Order Number": "1"}])

        def fake_fill(_path, log=None):
            import pandas as pd

            return pd.DataFrame([{"Order Number": "1", "Process and Item Number": "Process 3500 Item-1"}])

        def fake_split_pos(step3, wb, output_root, log=None):
            matched = Path(output_root) / "4_matched_split_and_assign_position_codes_3500.csv"
            matched.write_text("Order Number\n1\n", encoding="utf-8")

        def fake_assign(matched, shift, wb, output_root, **kwargs):
            p = Path(output_root) / "5_assign_process_number_3500.csv"
            p.write_text("Order Number,Process and Item Number\n1,Process 3500 Item-1\n", encoding="utf-8")

        def fake_split6(step5, output_root, wb, **kwargs):
            p = Path(output_root) / step6_name
            p.write_text("Order Number\n1\n", encoding="utf-8")

        def fake_excel(csv_path, output_root, dispatch_date, **kwargs):
            (Path(output_root) / f"{Path(csv_path).stem}.xlsx").write_bytes(b"PK")

        with patch("scripts.pipeline_runtime.runner.fetch_input_csv", side_effect=fake_fetch), patch(
            "scripts.pipeline_runtime.runner.write_fetched_csv", side_effect=fake_write
        ), patch(
            "scripts.pipeline_runtime.runner.apply_packing_rules_to_csv"
        ), patch(
            "scripts.pipeline_runtime.runner.enrich_packing_data", side_effect=fake_enrich
        ), patch(
            "scripts.pipeline_runtime.runner.fill_packing_columns", side_effect=fake_fill
        ), patch(
            "scripts.pipeline_runtime.runner.run_split_and_assign_position_codes",
            side_effect=fake_split_pos,
        ), patch(
            "scripts.pipeline_runtime.runner.run_assign_process_number", side_effect=fake_assign
        ), patch(
            "scripts.pipeline_runtime.runner.run_split_by_process_and_item_number",
            side_effect=fake_split6,
        ), patch(
            "scripts.pipeline_runtime.runner.filter_step6_csvs_for_missing_logos",
            side_effect=lambda csvs, **kw: (csvs, None, 0),
        ), patch(
            "scripts.pipeline_runtime.runner._update_all_orders_log"
        ), patch(
            "scripts.pipeline_runtime.runner.run_generate_excel_outputs", side_effect=fake_excel
        ), patch(
            "scripts.pipeline_runtime.runner.run_step8_pdf_generation_impl"
        ) as mock_s8:
            output_root, unmatched, missing, report = run_pipeline(
                **self._common_kwargs(), phases="excel"
            )

        mock_s8.assert_not_called()
        self.assertTrue(output_root.is_dir())
        self.assertTrue((output_root / step6_name).is_file())
        self.assertIsNone(report)


if __name__ == "__main__":
    unittest.main()
