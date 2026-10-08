from __future__ import annotations

import argparse
import re
from pathlib import Path

from scripts.app.pdf.merge_combined import (
    merge_combined_alternating,
    merge_combined_by_process,
    merge_combined_single_summary,
)


_PROCESS_PDF_RE = re.compile(r"process_(\d+)", re.IGNORECASE)


def _process_number_key_from_pdf_path(p: Path) -> int:
    m = _PROCESS_PDF_RE.search(p.stem)
    if not m:
        return 1_000_000_000
    try:
        return int(m.group(1))
    except Exception:
        return 1_000_000_000


def _existing_file(path_str: str) -> Path:
    p = Path(path_str)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"Path does not exist: {p}")
    if not p.is_file():
        raise argparse.ArgumentTypeError(f"Path is not a file: {p}")
    return p


def _existing_dir(path_str: str) -> Path:
    p = Path(path_str)
    if not p.exists():
        raise argparse.ArgumentTypeError(f"Path does not exist: {p}")
    if not p.is_dir():
        raise argparse.ArgumentTypeError(f"Path is not a directory: {p}")
    return p


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="recombine_from_process_pdfs",
        description="Rebuild a combined PDF from already-generated per-process PDFs (process_*.pdf).",
    )
    ap.add_argument(
        "--process-pdfs-dir",
        required=True,
        type=_existing_dir,
        help=r"Folder containing process_*.pdf files (e.g. output\Process_PDFs\2026-04-29\200).",
    )
    ap.add_argument(
        "--out-pdf",
        required=True,
        type=Path,
        help=r"Output combined PDF path (e.g. output\Combined_PDFs\2026-04-29\combined_TEST.pdf).",
    )
    ap.add_argument(
        "--mode",
        choices=["by_process", "single_summary", "alternating"],
        default="by_process",
        help="Combine behavior.",
    )
    ap.add_argument(
        "--missed-pdf",
        type=_existing_file,
        default=None,
        help="Optional PDF to append once at the end (e.g. a 'missed orders' page).",
    )
    ap.add_argument(
        "--batch-summary-pdf",
        type=_existing_file,
        default=None,
        help="Required for mode=single_summary. A PDF whose pages will be placed first.",
    )

    args = ap.parse_args(argv)

    per_process_pdfs = sorted(
        args.process_pdfs_dir.glob("process_*.pdf"),
        key=_process_number_key_from_pdf_path,
    )
    if not per_process_pdfs:
        ap.error(f"No files matching process_*.pdf found in: {args.process_pdfs_dir}")

    args.out_pdf.parent.mkdir(parents=True, exist_ok=True)

    missed_bytes = args.missed_pdf.read_bytes() if args.missed_pdf else None

    if args.mode == "by_process":
        merge_combined_by_process(out_path=args.out_pdf, per_process_pdfs=per_process_pdfs, missed_pdf_bytes=missed_bytes)
    elif args.mode == "alternating":
        if missed_bytes is not None:
            ap.error("--missed-pdf is only supported with --mode by_process")
        merge_combined_alternating(out_path=args.out_pdf, per_process_pdfs=per_process_pdfs)
    else:
        if args.batch_summary_pdf is None:
            ap.error("--batch-summary-pdf is required for --mode single_summary")
        if missed_bytes is not None:
            ap.error("--missed-pdf is only supported with --mode by_process")
        merge_combined_single_summary(
            out_path=args.out_pdf,
            batch_summary_pdf_bytes=args.batch_summary_pdf.read_bytes(),
            per_process_pdfs=per_process_pdfs,
        )

    print(f"Wrote combined PDF: {args.out_pdf}")
    print(f"Used {len(per_process_pdfs)} process PDFs from: {args.process_pdfs_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

