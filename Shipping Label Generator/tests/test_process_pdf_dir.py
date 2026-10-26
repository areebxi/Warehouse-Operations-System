from pathlib import Path

from scripts.app.flows.print_labels.batch_pdfs import _PROCESS_PDF_SAMPLE, _WIN_FILE_BUDGET, process_pdf_dir

_TODAY = (
    "B10-S2, B100-S2, B1050-S2, B1080-S2, B3500-S2, B3750-S2, B4000-S2, "
    "B4050-S2, B5080-S2, B5500-S2, B6000-S2, B8000-S2, B8050-S2, B90-S2, B9050-S2"
)


def test_short_key_keeps_the_readable_folder(tmp_path: Path) -> None:
    chosen = process_pdf_dir(tmp_path, "B100-S2")
    assert chosen == tmp_path / "B100-S2"


def test_long_key_shortens_under_windows_budget() -> None:
    base = Path("C:/") / ("a" * 120)
    chosen = process_pdf_dir(base, _TODAY)
    sample = chosen / _PROCESS_PDF_SAMPLE
    assert chosen.name != _TODAY
    assert len(chosen.name) == 12
    assert len(str(sample)) <= _WIN_FILE_BUDGET
