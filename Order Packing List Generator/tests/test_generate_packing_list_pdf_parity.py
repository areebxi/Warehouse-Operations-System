import tempfile
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pandas as pd

from scripts import generate_packing_list_pdf as gp
from scripts.pipeline_generate_packing_list_pdf.service import render_one_pdf_impl

_SVC = "scripts.pipeline_generate_packing_list_pdf.service"
_API = "scripts.pipeline_generate_packing_list_pdf.runtime_api"


class _FakeCanvas:
    created = []

    def __init__(self, filename, pagesize=None):
        self.filename = filename
        self.pagesize = pagesize
        self.title = None
        self.pages_shown = 0
        self.saved = False
        _FakeCanvas.created.append(self)

    def setTitle(self, title):
        self.title = title

    def showPage(self):
        self.pages_shown += 1

    def save(self):
        self.saved = True


class GeneratePackingListPdfParityTests(unittest.TestCase):
    def setUp(self):
        _FakeCanvas.created = []

    def test_csv_to_pdf_single_file_behavior(self):
        df = pd.DataFrame([{"Order Number": "A-1"}, {"Order Number": "A-2"}])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            apparel_dir = root / "apparel"
            logo_custom_dir = root / "logo_custom"
            logo_normal_dir = root / "logo_normal"
            apparel_dir.mkdir()
            logo_custom_dir.mkdir()
            logo_normal_dir.mkdir()
            csv_path = root / "input.csv"
            out_path = root / "output.pdf"

            build_map_mock = mock.MagicMock(
                side_effect=[
                    {"apparel_item": apparel_dir / "a.png"},
                    {"logo_custom_item": logo_custom_dir / "b.png"},
                    {"logo_normal_item": logo_normal_dir / "c.png"},
                ],
            )
            draw_page_mock = mock.MagicMock(side_effect=[(True, False), (False, True)])
            with (
                patch(f"{_SVC}.read_csv_with_order_numbers", return_value=df),
                patch.dict(
                    f"{_API}._CSV_STATIC",
                    {
                        "build_order_counts": mock.MagicMock(return_value={"A-1": 1, "A-2": 1}),
                        "build_process_totals": mock.MagicMock(return_value={"A-1": 1, "A-2": 1}),
                        "build_image_stem_map": build_map_mock,
                        "draw_page": draw_page_mock,
                    },
                ),
                patch(f"{_SVC}.canvas") as canvas_mod_mock,
            ):
                canvas_mod_mock.Canvas = _FakeCanvas
                n_pages, paths, missing_logo_df, missing_apparel_df = gp.csv_to_pdf(
                    csv_path,
                    out_path,
                    apparel_image_dir=apparel_dir,
                    logo_customise_dir=logo_custom_dir,
                    logo_normal_dir=logo_normal_dir,
                    apparel_stem_map=None,
                    logo_custom_stem_map=None,
                    logo_normal_stem_map=None,
                    position_code_to_draw=None,
                    show_process_item_count=True,
                )

            self.assertEqual(n_pages, 2)
            self.assertEqual(paths, [out_path])
            self.assertEqual(build_map_mock.call_count, 3)
            self.assertEqual(draw_page_mock.call_count, 2)
            self.assertEqual(len(_FakeCanvas.created), 1)
            self.assertTrue(_FakeCanvas.created[0].saved)
            self.assertEqual(_FakeCanvas.created[0].pages_shown, 2)
            self.assertIsNotNone(missing_logo_df)
            self.assertIsNotNone(missing_apparel_df)
            self.assertEqual(len(missing_logo_df), 1)
            self.assertEqual(len(missing_apparel_df), 1)

    def test_csv_to_pdf_passes_dispatch_date_to_draw_page(self):
        df = pd.DataFrame([{"Order Number": "A-1"}])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "input.csv"
            out_path = root / "output.pdf"

            draw_page_mock = mock.MagicMock(return_value=(False, False))
            with (
                patch(f"{_SVC}.read_csv_with_order_numbers", return_value=df),
                patch.dict(
                    f"{_API}._CSV_STATIC",
                    {
                        "build_order_counts": mock.MagicMock(return_value={"A-1": 1}),
                        "build_process_totals": mock.MagicMock(return_value={"A-1": 1}),
                        "draw_page": draw_page_mock,
                    },
                ),
                patch(f"{_SVC}.canvas") as canvas_mod_mock,
            ):
                canvas_mod_mock.Canvas = _FakeCanvas
                gp.csv_to_pdf(
                    csv_path,
                    out_path,
                    date_dd_mm_yyyy="11-06-2026",
                )

            draw_page_mock.assert_called_once()
            kwargs = draw_page_mock.call_args.kwargs
            self.assertEqual(kwargs["dispatch_date_label"], "11-06-2026")
            self.assertEqual(kwargs["dispatch_day_name"], "Thursday")

    def test_csv_to_pdf_split_behavior(self):
        df = pd.DataFrame([{"Order Number": f"A-{i}"} for i in range(51)])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = root / "input.csv"
            out_path = root / "output.pdf"

            with (
                patch(f"{_SVC}.read_csv_with_order_numbers", return_value=df),
                patch.dict(
                    f"{_API}._CSV_STATIC",
                    {
                        "build_order_counts": mock.MagicMock(return_value={}),
                        "draw_page": mock.MagicMock(return_value=(False, False)),
                    },
                ),
                patch(f"{_SVC}.canvas") as canvas_mod_mock,
            ):
                canvas_mod_mock.Canvas = _FakeCanvas
                n_pages, paths, missing_logo_df, missing_apparel_actual_df = gp.csv_to_pdf(
                    csv_path,
                    out_path,
                    show_process_item_count=False,
                )

            self.assertEqual(n_pages, 51)
            self.assertEqual(len(paths), 2)
            self.assertEqual(paths[0].name, "output_Part 1.pdf")
            self.assertEqual(paths[1].name, "output_Part 2.pdf")
            self.assertIsNone(missing_logo_df)
            self.assertIsNone(missing_apparel_actual_df)
            self.assertEqual(len(_FakeCanvas.created), 2)
            self.assertEqual(_FakeCanvas.created[0].pages_shown, 50)
            self.assertEqual(_FakeCanvas.created[1].pages_shown, 1)

    def test_render_one_pdf_formats_multiple_outputs(self):
        draw_map = {"X": "Front"}
        with patch.object(
            gp,
            "csv_to_pdf",
            return_value=(3, [Path("one.pdf"), Path("two.pdf")], None, None),
        ) as csv_to_pdf_mock:
            csv_name, pdf_name, n_pages, missing_logo_df, missing_apparel_df = render_one_pdf_impl(
                "input.csv",
                "out.pdf",
                None,
                None,
                None,
                draw_map,
                "11-06-2026",
                csv_to_pdf=csv_to_pdf_mock,
            )

        self.assertEqual(csv_name, "input.csv")
        self.assertEqual(pdf_name, "one.pdf, two.pdf")
        self.assertEqual(n_pages, 3)
        self.assertIsNone(missing_logo_df)
        self.assertIsNone(missing_apparel_df)
        self.assertEqual(csv_to_pdf_mock.call_args.kwargs["position_code_to_draw"], draw_map)
        self.assertEqual(csv_to_pdf_mock.call_args.kwargs["date_dd_mm_yyyy"], "11-06-2026")

    def test_main_delegates_to_main_impl_with_wrapper_dependencies(self):
        with patch.object(gp, "main_impl") as main_impl_mock:
            gp.main()

        main_impl_mock.assert_called_once()
        kwargs = main_impl_mock.call_args.kwargs
        self.assertEqual(kwargs["default_workbook"], gp.DEFAULT_WORKBOOK)
        self.assertIs(kwargs["build_image_stem_map"], gp._build_image_stem_map)
        self.assertIs(kwargs["load_position_code_to_draw"], gp.load_position_code_to_draw)
        self.assertIs(kwargs["csv_to_pdf"], gp.csv_to_pdf)
        self.assertIs(kwargs["format_missing_report"], gp.format_missing_report)


if __name__ == "__main__":
    unittest.main()
