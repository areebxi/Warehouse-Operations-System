from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# Path bootstrap + fixtures + grouping API live in test_grouping_fixtures.
from test_grouping_fixtures import (  # noqa: F401
    FIXED_BATCH_CODES,
    PERSONALISED_READY_TAG,
    RUN,
    Catalogs,
    Order,
    _cats,
    _cl_row,
    _fotl_cats,
    _gildan_tee_cats,
    _iron_cats,
    _order,
    _packs_row,
    _plain_row,
    _ready,
    _sweatshirt_cats,
    attrs_for_sku,
    finish_for_sku,
    group_orders,
    next_open_shift,
    next_plain_batch_codes,
    order_numbers_in_date_folder,
    six_field_core,
    slotify,
    write_process_csvs,
)

def test_write_process_csvs() -> None:
    from tempfile import TemporaryDirectory

    cat = _cats()
    r = group_orders(
        [
            _order("R1", "77989LG-M-T-BLK-M", tags=["1014-ALL-RESEND"], catalogs=cat),
            _order("B1", "77989LG-M-T-BLK-M", ship="", catalogs=cat),
            _order("U1", "NOPE-UNKNOWN", catalogs=cat),
            _order("G1", "77989LG-M-T-BLK-M", catalogs=cat),
        ],
        RUN,
    )
    with TemporaryDirectory() as td:
        root = Path(td)
        day = root / "11-09-2026"
        stale = day / "1st Shift"
        stale.mkdir(parents=True, exist_ok=True)
        (stale / "old-always-split.csv").write_text("stale\n", encoding="utf-8")
        paths = write_process_csvs(r, input_root=root)
        names = {p.name for p in paths}
        assert "RESEND.csv" in names
        assert "UNMATCHED.csv" in names
        assert any(n.startswith("B1-S1-PRINTED-") and n.endswith(".csv") for n in names)
        assert not (stale / "old-always-split.csv").exists()
        assert (day / "1st Shift" / "UNMATCHED.csv").is_file()
        assert not (day / "2nd Shift").exists()
        assert not (day / "3rd Shift").exists()
        text = (day / "1st Shift" / "RESEND.csv").read_text(encoding="utf-8")
        assert text.startswith("Order #,Ship By,Quantity,")
        assert "R1" in text
        unmatched = (day / "1st Shift" / "UNMATCHED.csv").read_text(encoding="utf-8")
        assert "U1" in unmatched
        assert "B1" not in unmatched
        process = next(p for p in paths if p.name.startswith("B1-S1-PRINTED-"))
        process_text = process.read_text(encoding="utf-8")
        assert "G1" in process_text
        assert "B1" in process_text  # blank ship-by → today
        second = day / "2nd Shift"
        second.mkdir(parents=True, exist_ok=True)
        keep = second / "keep-me.csv"
        keep.write_text("Order #\nOLD\n", encoding="utf-8")
        write_process_csvs(r, input_root=root)
        assert keep.is_file()
        assert keep.read_text(encoding="utf-8") == "Order #\nOLD\n"


