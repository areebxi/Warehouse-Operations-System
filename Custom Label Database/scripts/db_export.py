import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import os

# 1. Database Credentials
DB_USER = "root"
DB_PASS = "AaqY$#CGA5g3nDrx#49A"
DB_HOST = "78.46.128.21"
DB_PORT = "37005"
DB_NAME = "central_ecommerce_db"

# 2. Table Name Aur Output CSV File Path
# Jis table ko export karna hai uska naam daalein (e.g. 'product_catalog' ya 'customlabel_table')
TABLE_NAME = "Custom_Label_Database"

from pathlib import Path
import sys
_WAREHOUSE = Path(__file__).resolve().parents[2]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared.paths import cl_csv_path  # noqa: E402

OUTPUT_CSV_FILE = str(cl_csv_path())

try:
    print(f"⏳ Connecting to PostgreSQL database...")
    encoded_pass = quote_plus(DB_PASS)
    db_url = f"postgresql://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)

    print(f"⏳ Fetching data from table '{TABLE_NAME}'...")
    # PostgreSQL mixed-case table names require double quotes
    df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}";', con=engine)

    print(f"⏳ Saving data to CSV file: {OUTPUT_CSV_FILE}...")
    # CSV file me save karna
    df.to_csv(OUTPUT_CSV_FILE, index=False, encoding='utf-8')

    full_path = os.path.abspath(OUTPUT_CSV_FILE)
    print("\n" + "="*50)
    print(f"✅ SUCCESS! Table successfully exported.")
    print(f"📊 Total Rows Exported: {len(df)}")
    print(f"📁 Saved File Path: {full_path}")
    print("="*50)

except Exception as e:
    print("❌ Error exporting table to CSV:")
    print(e)