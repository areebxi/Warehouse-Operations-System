"""
Example configuration for Purchase Order Generator (BTC FTP / stock).

ShipStation credentials: config/ShipStation/.env (REAL_API_*).
Copy to config/PurchaseOrder/config.py for FTP settings.
"""

FTP_PROTOCOL = "sftp"
FTP_HOST = "sftpgo.btcactivewear.co.uk"
FTP_USER = "your_ftp_username"
FTP_PASS = "your_ftp_password"
FTP_PORT = 2022
FTP_REMOTE_FILE = "WebData/stock_levels_stock_id_fully_quoted.csv"
FTP_LOCAL_FILE = "stock_levels_stock_id_fully_quoted.csv"
FTP_TIMEOUT_SECONDS = 30
FTP_PASSIVE_MODE = True
FTP_MAX_RETRIES = 3
