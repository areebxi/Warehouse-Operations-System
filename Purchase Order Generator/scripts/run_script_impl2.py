from __future__ import annotations
import app_paths  # noqa: F401 — configures import paths before other local imports
from shipstation_orders import ShipStationAPI, ShipStationError
from pdf_generator import generate_packing_slips_for_tag
import sys
import os
import csv
import json
import socket
from datetime import datetime
from ftplib import FTP, error_perm, error_temp, error_reply
from app_paths import data_path, packs_database_path, shipstation_tags_path, tag_output_dir
from stock_resolver import (
    NOT_FOUND_STATUSES,
    STATUS_NOT_FOUND,
    load_custom_label_stock_map,
    not_found_status,
    resolve_stock_level,
)

def download_ftp_file(log=print):
    settings = _ftp_settings()
    ftp_host = settings["FTP_HOST"]
    ftp_user = settings["FTP_USER"]
    ftp_pass = settings["FTP_PASS"]
    ftp_port = int(settings["FTP_PORT"])
    server_filename, local_filename, local_basename = _stock_file_paths(settings)
    timeout_seconds = int(settings["FTP_TIMEOUT_SECONDS"])
    probe_timeout_seconds = int(settings.get("FTP_PROBE_TIMEOUT_SECONDS", 5))
    passive_mode = bool(settings["FTP_PASSIVE_MODE"])
    max_retries = max(1, int(settings["FTP_MAX_RETRIES"]))
    protocol = _stock_transfer_protocol(settings, ftp_port)

    if protocol == "ftp" and ftp_port == 22:
        log(
            "[WARNING] Port 22 is SFTP, not FTP. "
            "Set FTP_PROTOCOL = 'sftp' and FTP_HOST = 'sftpgo.btcactivewear.co.uk', "
            "or use FTP_PORT = 21 with ftpdata.btcactivewear.co.uk."
        )
        protocol = "sftp"

    log_label = "SFTP" if protocol == "sftp" else "FTP"
    log(f"[INFO] Downloading stock file via {log_label}...")
    log(
        f"[INFO] Stock file: remote={server_filename} → local={local_filename} "
        f"(config: FTP_REMOTE_FILE / FTP_LOCAL_FILE in config.py)"
    )
    log(f"[INFO] {log_label} host: {ftp_host}:{ftp_port} (timeout={timeout_seconds}s)")

    log(f"[INFO] Checking TCP reachability to {ftp_host}:{ftp_port}...")
    if not _ftp_probe_tcp(ftp_host, ftp_port, probe_timeout_seconds):
        log(_stock_transfer_blocked_message(ftp_host, ftp_port, protocol))
        has_cache = _log_cached_stock_file(local_filename, log=log)
        if has_cache:
            log(f"[INFO] Continuing with cached {os.path.basename(local_filename)} for stock checks.")
        else:
            log(f"[WARNING] No cached {os.path.basename(local_filename)} found. Stock checks will be skipped.")
        return False

    if protocol == "sftp":
        if _download_sftp_file(
            ftp_host,
            ftp_port,
            ftp_user,
            ftp_pass,
            server_filename,
            local_filename,
            timeout_seconds,
            max_retries,
            log=log,
        ):
            return True
        _log_cached_stock_file(local_filename, log=log)
        return False

    log(f"[INFO] FTP passive mode: {passive_mode}")
    last_error = None
    for attempt in range(1, max_retries + 1):
        ftp = None
        try:
            if attempt > 1:
                log(f"[INFO] FTP retry {attempt}/{max_retries}...")
            ftp = FTP(timeout=timeout_seconds)
            ftp.connect(ftp_host, ftp_port, timeout=timeout_seconds)
            ftp.login(ftp_user, ftp_pass)
            ftp.set_pasv(passive_mode)
            log(f"[SUCCESS] Connected to FTP server '{ftp_host}'.")

            with open(local_filename, "wb") as f:
                ftp.retrbinary(f"RETR {server_filename}", f.write)
            log(f"[SUCCESS] Downloaded {server_filename} → {local_filename}")
            return True
        except (error_perm, error_temp, error_reply, socket.timeout, TimeoutError, ConnectionRefusedError, OSError) as e:
            last_error = e
            log(f"[ERROR] FTP attempt {attempt}/{max_retries} failed: {e}")
        except FileNotFoundError:
            log(f"[ERROR] Cannot write local file '{local_filename}'. Check folder permissions.")
            return False
        except Exception as e:
            last_error = e
            log(f"[ERROR] Unexpected FTP error (attempt {attempt}/{max_retries}): {e}")
        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception as e:
                    log(f"[WARNING] Error in FTP disconnection: {e}")

    log(
        f"[ERROR] Could not download free stock via FTP. "
        f"Port {ftp_port} to {ftp_host} must be allowed on your network/firewall "
        "(or use VPN if required by BTC)."
    )
    if last_error:
        log(f"[ERROR] Last FTP error: {last_error}")
    _log_cached_stock_file(local_filename, log=log)
    return False
def normalize_packing_rows(in_stock_items):
    """Normalize in-stock rows to packing list CSV format (11 columns)."""
    normalized_rows = []
    for row in in_stock_items:
        # Not-found issue rows may include Status as a 10th field.
        if len(row) == 10 and str(row[9]) in NOT_FOUND_STATUSES:
            row = row[:9]
        if len(row) == 8:
            order_number, recipient_name, quantity, sku, tag_id, stock_level, pno, marketplace = row
            normalized_rows.append(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    sku,
                    "",
                    tag_id,
                    stock_level,
                    "",
                    "",
                    pno,
                    marketplace,
                ]
            )
        elif len(row) == 11:
            normalized_rows.append(row)
        elif len(row) == 10:
            normalized_rows.append(list(row) + [""])
        elif len(row) == 9:
            (
                order_number,
                recipient_name,
                quantity,
                item_sku,
                complete_sku,
                stock_id,
                tag_id,
                stock_level,
                pno,
            ) = row
            packing_sku = stock_id if stock_id else item_sku
            normalized_rows.append(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    packing_sku,
                    "",
                    tag_id,
                    stock_level,
                    "",
                    "",
                    pno,
                    complete_sku,
                ]
            )
        elif len(row) == 7:
            order_number, recipient_name, quantity, sku, tag_id, stock_level, pno = row
            normalized_rows.append(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    sku,
                    "",
                    tag_id,
                    stock_level,
                    "",
                    "",
                    pno,
                    "",
                ]
            )
        else:
            normalized_rows.append(row)
    return normalized_rows
def _pack_key(sku: str) -> str:
    sku = (sku or "").strip()
    return sku.split("-", 1)[0] if "-" in sku else sku
