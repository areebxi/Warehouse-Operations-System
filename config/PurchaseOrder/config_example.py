"""
Example configuration for Purchase Order Generator (BTC FTP / stock).

ShipStation API credentials are NOT here — use config/ShipStation/.env:
  REAL_API_BASE_URL=https://ssapi.shipstation.com
  REAL_API_KEY=...
  REAL_API_SECRET=...

Copy this file to config/PurchaseOrder/config.py and fill FTP values.
"""

# BTC stock download — see FOLDER_LAYOUT.md → "Changing the BTC stock file"
#
# Option A — classic FTP:
#   FTP_PROTOCOL = "ftp"
#   FTP_HOST = "ftpdata.btcactivewear.co.uk"
#   FTP_PORT = 21
#
# Option B — SFTP (BTC SFTPGo):
#   FTP_PROTOCOL = "sftp"
#   FTP_HOST = "sftpgo.btcactivewear.co.uk"
#   FTP_PORT = 2022
#
# Stock CSV — change FTP_REMOTE_FILE (server path) and FTP_LOCAL_FILE (data/ filename):
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
