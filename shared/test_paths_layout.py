"""ponytail: layout self-check — fails if app-owned paths drift back to warehouse roots."""

from __future__ import annotations

from shared import paths as wh


def main() -> None:
    root = wh.warehouse_root()
    pack = wh.packing_app_dir()
    queue = wh.queue_app_dir()
    ship = wh.shipping_app_dir()
    po = wh.po_app_dir()

    assert wh.packing_data_dir() == pack / "Data"
    assert wh.packing_output_dir() == pack / "Output"
    assert wh.packing_config_dir() == pack / "config"
    assert wh.queue_config_workbook_path() == queue / "config" / "Configuration Workbook.xlsx"
    assert wh.queue_output_dir() == queue / "Output"
    assert wh.shipping_yaml_path() == ship / "shipping_config.yaml"
    assert wh.shipping_desfiles_dir() == ship / "DTF Des Files"
    assert wh.po_data_dir() == po / "data"
    assert wh.images_po_dir() == po / "assets"
    assert wh.po_output_dir() == po / "output"
    assert wh.po_config_py_path() == po / "config.py"

    # Shared joins stay outside apps
    assert wh.product_export_path().is_relative_to(root / "data")
    assert wh.shipstation_tags_path().is_relative_to(root / "data")
    assert wh.shipstation_env_path().is_relative_to(root / "config" / "ShipStation")
    assert wh.shared_inbox_dtf_des_root().is_relative_to(root / "runtime" / "SharedInbox")
    print("paths layout ok")


if __name__ == "__main__":
    main()
