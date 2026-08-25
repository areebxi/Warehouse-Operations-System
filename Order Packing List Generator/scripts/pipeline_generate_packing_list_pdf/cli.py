import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd


def main_impl(
    *,
    default_workbook: Path,
    build_image_stem_map: Callable[[Optional[Path], bool], Dict[str, Path]],
    load_position_code_to_draw: Callable[[Path], Dict[str, str]],
    csv_to_pdf: Callable[..., Tuple[int, List[Path], Optional[pd.DataFrame], Optional[pd.DataFrame]]],
    format_missing_report: Callable[[Optional[pd.DataFrame], Optional[pd.DataFrame]], Optional[str]],
) -> None:
    parser = argparse.ArgumentParser(
        description="Generate packing list PDFs from step-6 CSV(s). Optional image dirs embed apparel and logo images.",
        epilog="Without --apparel-dir/--logo-normal-dir/--logo-custom-dir, image slots show placeholders (A/L).",
    )
    parser.add_argument("input_path", type=Path, help="Path to a step-6 CSV file or directory of step-6 CSVs")
    parser.add_argument("output_path", type=Path, nargs="?", default=None, help="Output PDF path or directory (default: same as input)")
    parser.add_argument("--apparel-dir", type=Path, default=None, metavar="DIR", help="Apparel image folder (top-level only)")
    parser.add_argument("--logo-normal-dir", type=Path, default=None, metavar="DIR", help="Normal logo/design image folder (top-level only)")
    parser.add_argument("--logo-custom-dir", type=Path, default=None, metavar="DIR", help="Customise logo/design image folder (searched recursively)")
    parser.add_argument("--workbook", type=Path, default=None, metavar="XLSX", help="Workbook with Process Info Sheet (for Draw-based logo overlays)")
    parser.add_argument(
        "--date",
        type=str,
        default=date.today().strftime("%d-%m-%Y"),
        metavar="DD-MM-YYYY",
        help="Dispatch date shown on each PDF page (default: today)",
    )
    args = parser.parse_args()

    input_path = args.input_path
    output_path = args.output_path

    apparel_dir_path = args.apparel_dir if args.apparel_dir else None
    logo_normal_path = args.logo_normal_dir if args.logo_normal_dir else None
    logo_custom_path = args.logo_custom_dir if args.logo_custom_dir else None
    workbook_path = args.workbook if args.workbook is not None else default_workbook

    apparel_stem_map: Optional[Dict[str, Path]] = None
    logo_normal_stem_map: Optional[Dict[str, Path]] = None
    logo_custom_stem_map: Optional[Dict[str, Path]] = None
    if apparel_dir_path is not None or logo_normal_path is not None or logo_custom_path is not None:
        with ThreadPoolExecutor(max_workers=3) as executor:
            fut_apparel = executor.submit(build_image_stem_map, apparel_dir_path, recursive=False)
            fut_logo_normal = executor.submit(build_image_stem_map, logo_normal_path, recursive=False)
            fut_logo_custom = executor.submit(build_image_stem_map, logo_custom_path, recursive=True)
            apparel_stem_map = fut_apparel.result()
            logo_normal_stem_map = fut_logo_normal.result()
            logo_custom_stem_map = fut_logo_custom.result()
    else:
        print("Note: No image directories given; PDFs will show placeholders (A/L) for image slots.", file=sys.stderr)

    position_code_to_draw = load_position_code_to_draw(workbook_path) if workbook_path.exists() else {}

    def do_csv_to_pdf(csv_path: Path, pdf_path: Path):
        return csv_to_pdf(
            csv_path,
            pdf_path,
            apparel_image_dir=apparel_dir_path,
            logo_customise_dir=logo_custom_path,
            logo_normal_dir=logo_normal_path,
            apparel_stem_map=apparel_stem_map,
            logo_custom_stem_map=logo_custom_stem_map,
            logo_normal_stem_map=logo_normal_stem_map,
            position_code_to_draw=position_code_to_draw,
            date_dd_mm_yyyy=args.date,
        )

    if input_path.is_file():
        if input_path.suffix.lower() != ".csv":
            print("Input must be a CSV file or a directory.", file=sys.stderr)
            raise SystemExit(1)
        out = output_path if output_path and output_path.suffix.lower() == ".pdf" else input_path.with_suffix(".pdf")
        if output_path and output_path.is_dir():
            out = output_path / input_path.with_suffix(".pdf").name
        n_pages, paths, missing_logo_actual, missing_apparel_actual = do_csv_to_pdf(input_path, out)
        if not paths:
            print(f"No pages written for {input_path} ({n_pages} pages)")
        elif len(paths) == 1:
            print(f"Wrote {paths[0]} ({n_pages} pages)")
        else:
            joined = ", ".join(str(p) for p in paths)
            print(f"Wrote {joined} ({n_pages} pages)")
        report = format_missing_report(missing_logo_actual, missing_apparel_actual)
        if report:
            print(report)
        return

    if not input_path.is_dir():
        print("Input path not found or not a file/directory.", file=sys.stderr)
        raise SystemExit(1)
    out_dir = output_path if output_path and output_path.is_dir() else input_path
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_files = sorted(input_path.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in directory.", file=sys.stderr)
        raise SystemExit(1)
    all_missing_logo_actual: List[pd.DataFrame] = []
    all_missing_apparel_actual: List[pd.DataFrame] = []
    for csv_path in csv_files:
        pdf_name = csv_path.with_suffix(".pdf").name
        pdf_path = out_dir / pdf_name
        n_pages, paths, missing_logo_actual, missing_apparel_actual = do_csv_to_pdf(csv_path, pdf_path)
        if missing_logo_actual is not None and not missing_logo_actual.empty:
            all_missing_logo_actual.append(missing_logo_actual)
        if missing_apparel_actual is not None and not missing_apparel_actual.empty:
            all_missing_apparel_actual.append(missing_apparel_actual)
        display = ", ".join(p.name for p in paths) if len(paths) > 1 else (paths[0].name if paths else pdf_path.name)
        print(f"  {csv_path.name} -> {display} ({n_pages} pages)")
    print(f"Wrote {len(csv_files)} PDF(s) to {out_dir}")
    missing_logo_combined = (
        pd.concat(all_missing_logo_actual, ignore_index=True) if all_missing_logo_actual else None
    )
    missing_apparel_combined = (
        pd.concat(all_missing_apparel_actual, ignore_index=True) if all_missing_apparel_actual else None
    )
    report = format_missing_report(missing_logo_combined, missing_apparel_combined)
    if report:
        print(report)
