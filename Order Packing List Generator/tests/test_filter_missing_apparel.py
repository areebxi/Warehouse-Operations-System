"""Missing-apparel sideline CSV from the Step 5→6 image filter."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts.pipeline_runtime.filter_missing_logos import filter_step6_csvs_for_missing_logos


def test_filter_missing_apparel_writes_sideline_and_keeps_ok(tmp_path: Path):
    csv_path = tmp_path / "5_assign_process_number_tok.csv"
    df = pd.DataFrame(
        {
            "Order Number": ["A1", "B1"],
            "Item Quantity": [1, 1],
            "Customise": ["No", "No"],
            "Item SKU": ["SKU-A", "SKU-B"],
            "Logo/Design Image": ["TOK-OK", "TOK-OK"],
            "Apparel Image": ["APP-MISS", "APP-OK"],
            "Picture Name": ["", ""],
        }
    )
    df.to_csv(csv_path, index=False, encoding="utf-8")

    def fake_flag(frame, **_kw):
        miss_apparel = frame["Apparel Image"].astype(str).eq("APP-MISS")
        return pd.Series(False, index=frame.index), miss_apparel

    with (
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.build_preflight_stem_maps",
            return_value=(
                {"APP-OK": tmp_path / "a.png"},
                {"TOK-OK": tmp_path / "ok.png"},
                None,
                tmp_path,
                tmp_path,
                None,
                None,
            ),
        ),
        patch(
            "scripts.pipeline_runtime.filter_missing_logos.flag_missing_images",
            side_effect=fake_flag,
        ),
    ):
        kept, logo_path, apparel_path, n_excluded = filter_step6_csvs_for_missing_logos(
            [csv_path],
            output_root=tmp_path,
            token="tok",
            logo_custom_single_dir=None,
            logo_custom_double_dir=None,
            logo_normal_dir=tmp_path,
            apparel_dir=tmp_path,
        )

    assert n_excluded == 0
    assert logo_path is None
    assert apparel_path is not None and apparel_path.exists()
    reported = pd.read_csv(apparel_path)
    assert reported["Order Number"].tolist() == ["A1"]
    assert len(kept) == 1
    assert pd.read_csv(kept[0])["Order Number"].tolist() == ["A1", "B1"]
