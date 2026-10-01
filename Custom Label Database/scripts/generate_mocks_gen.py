"""Row generation from mocks + BTC Product Data."""
from __future__ import annotations

from collections import Counter

import pandas as pd

from generate_mocks_util import (
    SEED_COLS,
    apparel_image_slug,
    clean,
    gender_apparel_from_pe,
    map_print_positions,
    normalize_colour,
    normalize_size,
    split_product_codes,
)


def generate_rows(
    mocks: pd.DataFrame,
    pe: pd.DataFrame,
    skip_mock_ids: set[str],
    only_mocks: set[str] | None,
) -> tuple[pd.DataFrame, dict]:
    pe_by_spc: dict[str, pd.DataFrame] = {
        spc: grp for spc, grp in pe.groupby("SPC", sort=False) if clean(spc)
    }

    stats: dict = Counter()
    skip_reasons: dict[str, str] = {}
    rows: list[dict] = []

    for _, mock in mocks.iterrows():
        mock_id = clean(mock["Pasting Mocks ID"]).upper()
        if only_mocks and mock_id not in only_mocks:
            continue

        if mock_id in skip_mock_ids:
            stats["skipped_mock_already_in_db"] += 1
            skip_reasons[mock_id] = "mock already in Custom Label Database"
            continue

        product_code = clean(mock.get("Product Code", ""))
        printing_pos = clean(mock.get("Printing Position", ""))
        codes = split_product_codes(product_code)

        if not codes:
            stats["skipped_mock_no_product_code"] += 1
            skip_reasons[mock_id] = "no Product Code"
            continue

        pp = map_print_positions(printing_pos, mock_id)
        if not pp:
            stats["skipped_mock_no_print_pos"] += 1
            skip_reasons[mock_id] = f"unmapped/blank Printing Position: {printing_pos!r}"
            continue

        variants: list[pd.Series] = []
        for code in codes:
            grp = pe_by_spc.get(code)
            if grp is None or grp.empty:
                stats["product_code_no_pe"] += 1
                continue
            variants.append(grp)

        if not variants:
            stats["skipped_mock_no_pe_hits"] += 1
            skip_reasons[mock_id] = f"no BTC Product Data SPC hits for {codes}"
            continue

        pe_hits = pd.concat(variants, ignore_index=True).drop_duplicates(subset=["UID"])
        mock_new = 0
        mock_skip_ga = 0
        mock_skip_fields = 0

        for _, pe_row in pe_hits.iterrows():
            uid = clean(pe_row["UID"])
            brand_code = clean(pe_row.get("Brand Code", ""))
            desc = clean(pe_row.get("Description", ""))
            colour = normalize_colour(pe_row.get("Colour Name", ""))
            size = normalize_size(pe_row.get("Size", ""))
            ga = gender_apparel_from_pe(brand_code, desc)

            if not ga:
                mock_skip_ga += 1
                stats["skipped_uid_no_gender_apparel"] += 1
                continue

            apparel_image = apparel_image_slug(ga, colour)
            custom_label = f"{mock_id}-{uid}"

            if not all([custom_label, ga, colour, size, apparel_image, pp]):
                mock_skip_fields += 1
                stats["skipped_uid_incomplete_seeds"] += 1
                continue

            rows.append(
                {
                    "Custom Label": custom_label,
                    "Gender Apparel": ga,
                    "Colour": colour,
                    "Size": size,
                    "Apparel Image": apparel_image,
                    "Print Positions": pp,
                }
            )
            mock_new += 1

        if mock_new == 0:
            stats["skipped_mock_zero_rows"] += 1
            skip_reasons[mock_id] = (
                f"0 rows after filters (PE={len(pe_hits)}, "
                f"no_GA={mock_skip_ga}, incomplete={mock_skip_fields})"
            )
        else:
            stats["mocks_generated"] += 1
            stats["rows_generated"] += mock_new
            stats[f"rows_{mock_id}"] = mock_new

    out = pd.DataFrame(rows, columns=SEED_COLS)
    return out, {"counts": dict(stats), "skip_reasons": skip_reasons}
