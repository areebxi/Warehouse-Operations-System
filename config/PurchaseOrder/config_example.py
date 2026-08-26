"""
Example configuration file for ShipStation API credentials
Copy this file to config.py and update with your actual credentials
"""

# ShipStation API Configuration
# Get these from your ShipStation account settings
SHIPSTATION_API_KEY = "your_api_key_here"
SHIPSTATION_API_SECRET = "your_api_secret_here"

# How to get your API credentials:
# 1. Log in to your ShipStation account
# 2. Go to Settings > API Settings
# 3. Generate or copy your API Key and API Secret
# 4. Replace the values above with your actual credentials

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
