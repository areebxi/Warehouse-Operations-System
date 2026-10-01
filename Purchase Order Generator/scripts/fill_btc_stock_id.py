"""Fill BTC Stock ID on Custom Label from BTC Product Data — stable façade."""

from __future__ import annotations

import sys
from pathlib import Path

_WAREHOUSE = Path(__file__).resolve().parents[2]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))

from shared import paths as wh  # noqa: E402

from fill_btc_stock_id_lookup import (  # noqa: E402
    build_lookup,
    fill_stock_ids,
    load_csv,
    lookup_uid,
    write_csv,
)
from fill_btc_stock_id_main import main as _main  # noqa: E402
from fill_btc_stock_id_maps import cl_size_to_pe, colours_to_try, norm  # noqa: E402

DEFAULT_CUSTOM_LABEL = wh.cl_csv_path()
DEFAULT_BTC_PRODUCT_DATA = wh.btc_product_data_path()


def main() -> int:
    return _main(
        default_custom_label=DEFAULT_CUSTOM_LABEL,
        default_btc_product_data=DEFAULT_BTC_PRODUCT_DATA,
    )


if __name__ == "__main__":
    raise SystemExit(main())
