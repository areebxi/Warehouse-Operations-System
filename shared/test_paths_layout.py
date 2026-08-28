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
    assert wh.po_gui_settings_path().is_relative_to(wh.po_app_dir() / "config")
    assert wh.cl_csv_path() == db / "shared" / "custom_label" / "Custom_Label_Database.csv"
    assert wh.custom_label_support_dir() == db / "custom-label-database" / "support"
    assert wh.images_apparel_dir() == db / "custom-label-database" / "Apparel Images"
    assert wh.product_export_path() == db / "shared" / "product_export" / "ProductExport.csv"
    assert wh.shipstation_tags_path() == db / "shared" / "shipstation" / "ShipStation_Tags.xlsx"
    assert wh.shipstation_env_path().is_relative_to(root / "config" / "ShipStation")
    assert wh.shared_inbox_dtf_des_root().is_relative_to(root / "runtime" / "SharedInbox")
    print("paths layout ok")


if __name__ == "__main__":
    main()
