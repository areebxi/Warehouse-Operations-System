"""ponytail: layout self-check — fails if database paths drift back into app folders."""

from __future__ import annotations

from shared import paths as wh


def main() -> None:
    root = wh.warehouse_root()
    db = wh.database_root()

    assert wh.packing_data_dir() == db / "order-packing-list-generator"
    assert wh.packing_workbook_path() == db / "order-packing-list-generator" / "Workbook.xlsx"
    assert wh.queue_config_workbook_path() == db / "production-design-queue-manager" / "Configuration Workbook.xlsx"
    assert wh.po_data_dir() == db / "purchase-order-generator"
    assert wh.plain_database_path() == db / "shared" / "plain" / "Plain Database.xlsx"
    assert wh.packs_database_path() == db / "shared" / "packs" / "Packs Database.xlsx"
    assert wh.po_database_path() == wh.plain_database_path()
    assert wh.po_packs_database_path() == wh.packs_database_path()
    assert wh.po_gui_settings_path().is_relative_to(wh.po_app_dir() / "config")
    assert wh.cl_csv_path() == db / "shared" / "custom_label" / "Custom_Label_Database.csv"
    assert wh.custom_label_support_dir() == db / "custom-label-database" / "support"
    assert wh.images_apparel_dir() == db / "custom-label-database" / "Apparel Images"
    assert wh.btc_product_data_path() == db / "shared" / "btc_product_data" / "BTC_Product_Data.csv"
    assert wh.uneek_product_data_path() == db / "shared" / "uneek_product_data" / "Uneek_Product_Data.xlsx"
    assert wh.absolute_product_data_path() == db / "shared" / "absolute_product_data" / "Absolute_Product_Data.xlsx"
    assert wh.size_references_csv_path() == db / "custom-label-database" / "support" / "Size References.csv"
    assert wh.mocks_database_csv_path() == db / "custom-label-database" / "support" / "Mocks Database.csv"
    assert wh.shipstation_tags_path() == db / "shared" / "shipstation_tags" / "ShipStation_Tags.xlsx"
    assert wh.shipstation_env_path().is_relative_to(root / "config" / "ShipStation")
    assert wh.shared_inbox_dtf_des_root().is_relative_to(root / "runtime" / "SharedInbox")
    assert wh.sorter_app_dir() == root / "Order Grouping Sorter"
    assert wh.sorter_data_dir() == db / "order-grouping-sorter"
    assert wh.sorter_catalog_cache_dir() == db / "order-grouping-sorter" / "catalog_cache"
    assert wh.sorter_catalog_cache_path("plain") == (
        db / "order-grouping-sorter" / "catalog_cache" / "plain.pkl"
    )
    assert wh.sorter_logs_dir() == root / "Order Grouping Sorter" / "Logs"
    assert wh.sorter_input_csv_path("11-09-2026", "1st Shift", "today-1st-plain") == (
        root / "Order Packing List Generator" / "Input" / "11-09-2026" / "1st Shift" / "today-1st-plain.csv"
    )
    print("paths layout ok")


if __name__ == "__main__":
    main()
