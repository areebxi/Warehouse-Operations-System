"""BTC FTP/SFTP settings and stock file path helpers."""
from __future__ import annotations

import os
import socket

from app_paths import data_path


def _ftp_settings():
    """Resolve FTP settings from config.py with safe defaults."""
    defaults = {
        "FTP_HOST": "ftpdata.btcactivewear.co.uk",
        "FTP_USER": "daa0001",
        "FTP_PASS": "#T/Yn7pePnPC",
        "FTP_PORT": 21,
        "FTP_PROTOCOL": "ftp",
        "FTP_REMOTE_FILE": "WebData/stock_levels_stock_id_fully_quoted.csv",
        "FTP_LOCAL_FILE": "stock_levels_stock_id_fully_quoted.csv",
        "FTP_TIMEOUT_SECONDS": 30,
        "FTP_PROBE_TIMEOUT_SECONDS": 5,
        "FTP_PASSIVE_MODE": True,
        "FTP_MAX_RETRIES": 3,
    }
    try:
        import config as app_config

        for key, default in defaults.items():
            defaults[key] = getattr(app_config, key, default)
    except Exception:
        pass
    return defaults


def _stock_file_paths(settings=None):
    """Remote path on BTC server, local path under data/, and local filename."""
    settings = settings or _ftp_settings()
    remote_file = settings["FTP_REMOTE_FILE"]
    local_basename = os.path.basename(settings["FTP_LOCAL_FILE"])
    local_path = settings["FTP_LOCAL_FILE"]
    if not os.path.isabs(local_path):
        local_path = str(data_path(local_basename))
    return remote_file, local_path, local_basename


def _ftp_probe_tcp(host: str, port: int, timeout_seconds: int) -> bool:
    """Quick TCP check before full FTP attempts."""
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def _stock_transfer_protocol(settings: dict, ftp_port: int) -> str:
    protocol = str(settings.get("FTP_PROTOCOL", "ftp")).strip().lower()
    if protocol in ("ftp", "sftp"):
        return protocol
    if ftp_port in (22, 2022):
        return "sftp"
    return "ftp"


def _stock_transfer_blocked_message(host: str, port: int, protocol: str) -> str:
    _, local_path, local_name = _stock_file_paths()
    manual_hint = (
        f"or manually download {local_name} into the data/ folder "
        f"(set FTP_LOCAL_FILE in config.py)."
    )
    if protocol == "sftp":
        return (
            f"[ERROR] Cannot reach {host}:{port} (timed out). "
            f"Your network or firewall is blocking outbound SFTP (TCP port {port}). "
            f"Ask IT to allow port {port} to {host}, use a BTC-approved VPN, "
            f"{manual_hint}"
        )
    return (
        f"[ERROR] Cannot reach {host}:{port} (timed out). "
        f"Your network or firewall is blocking outbound FTP (TCP port {port}). "
        f"Ask IT to allow port {port} to {host}, use a BTC-approved VPN, "
        f"{manual_hint}"
    )
