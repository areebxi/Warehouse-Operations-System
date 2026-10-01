from __future__ import annotations

from pathlib import Path

from shared.paths.catalog import custom_label_database_dir
from shared.paths.po import po_app_dir
from shared.paths.root import config_root, runtime_root, warehouse_root_from

def shipstation_config_dir(from_path: object | None = None) -> Path:
    return config_root(from_path) / "ShipStation"


def shipstation_env_path(from_path: object | None = None) -> Path:
    """Warehouse ShipStation secrets file (REAL_API_*)."""
    return shipstation_config_dir(from_path) / ".env"


# --- Shared Inbox / images ---


def shared_inbox_dtf_des_root(from_path: object | None = None) -> Path:
    return runtime_root(from_path) / "SharedInbox" / "DTF Des"


def images_apparel_dir(from_path: object | None = None) -> Path:
    return custom_label_database_dir(from_path) / "Apparel Images"


def demo_images_root(from_path: object | None = None) -> Path:
    """Testing-mode placeholders (apparel + logo folders)."""
    return warehouse_root_from(from_path) / "Demo Images Database"


def demo_apparel_dir(from_path: object | None = None) -> Path:
    return demo_images_root(from_path) / "Product Images"


def demo_normal_design_dir(from_path: object | None = None) -> Path:
    return demo_images_root(from_path) / "Normal Designs"


def demo_custom_single_dir(from_path: object | None = None) -> Path:
    return demo_images_root(from_path) / "Personalized Designs" / "Single Position"


def demo_custom_double_dir(from_path: object | None = None) -> Path:
    return demo_images_root(from_path) / "Personalized Designs" / "Double Position"


def images_po_dir(from_path: object | None = None) -> Path:
    return po_app_dir(from_path) / "assets"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

__all__ = [
    "shipstation_config_dir",
    "shipstation_env_path",
    "shared_inbox_dtf_des_root",
    "images_apparel_dir",
    "demo_images_root",
    "demo_apparel_dir",
    "demo_normal_design_dir",
    "demo_custom_single_dir",
    "demo_custom_double_dir",
    "images_po_dir",
    "ensure_dir",
]
