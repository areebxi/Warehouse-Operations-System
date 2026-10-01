"""Download BTC free-stock file via FTP/SFTP."""
from __future__ import annotations

import os
import socket
from datetime import datetime
from ftplib import FTP, error_perm, error_reply, error_temp

from run_ftp_settings import (
    _ftp_probe_tcp,
    _ftp_settings,
    _stock_file_paths,
    _stock_transfer_blocked_message,
    _stock_transfer_protocol,
)


def _download_sftp_file(
    host: str,
    port: int,
    username: str,
    password: str,
    remote_file: str,
    local_filename: str,
    timeout_seconds: int,
    max_retries: int,
    log=print,
) -> bool:
    try:
        import paramiko
    except ImportError:
        log(
            "[ERROR] SFTP download requires the 'paramiko' package. "
            "Run: pip install paramiko"
        )
        return False

    last_error = None
    for attempt in range(1, max_retries + 1):
        transport = None
        sftp = None
        try:
            if attempt > 1:
                log(f"[INFO] SFTP retry {attempt}/{max_retries}...")
            transport = paramiko.Transport((host, port))
            transport.banner_timeout = timeout_seconds
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            log(f"[SUCCESS] Connected to SFTP server '{host}'.")
            sftp.get(remote_file, local_filename)
            log(f"[SUCCESS] Downloaded {remote_file} → {local_filename}")
            return True
        except Exception as e:
            last_error = e
            log(f"[ERROR] SFTP attempt {attempt}/{max_retries} failed: {e}")
        finally:
            if sftp is not None:
                try:
                    sftp.close()
                except Exception:
                    pass
            if transport is not None:
                try:
                    transport.close()
                except Exception:
                    pass

    if last_error:
        log(f"[ERROR] Last SFTP error: {last_error}")
    return False


def _log_cached_stock_file(local_filename: str, log=print) -> bool:
    if not os.path.isfile(local_filename):
        return False
    modified = datetime.fromtimestamp(os.path.getmtime(local_filename))
    age_hours = (datetime.now() - modified).total_seconds() / 3600
    size_kb = os.path.getsize(local_filename) // 1024
    log(
        f"[WARNING] Using cached {local_filename} from {modified:%Y-%m-%d %H:%M} "
        f"({age_hours:.1f} hours old, {size_kb} KB). Stock checks may be outdated."
    )
    return True


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
