"""Export NocoDB/Postgres Custom_Label_Database → live warehouse CSV."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.paths import cl_csv_path  # noqa: E402

# Credentials stay in this script (do not paste into docs/chat).
DB_USER = "root"
DB_PASS = "AaqY$#CGA5g3nDrx#49A"
DB_HOST = "78.46.128.21"
DB_PORT = "37005"
DB_NAME = "central_ecommerce_db"
TABLE_NAME = "Custom_Label_Database"


def main() -> int:
    out = cl_csv_path(ROOT)
    out.parent.mkdir(parents=True, exist_ok=True)

    print("Connecting to PostgreSQL...")
    encoded_pass = quote_plus(DB_PASS)
    # Explicit driver: SQLAlchemy 2.x defaults to psycopg (v3); we use psycopg2.
    db_url = (
        f"postgresql+psycopg2://{DB_USER}:{encoded_pass}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(db_url)

    print(f"Fetching table '{TABLE_NAME}'...")
    # Mixed-case Postgres identifiers need double quotes.
    df = pd.read_sql_query(f'SELECT * FROM "{TABLE_NAME}";', con=engine)

    print(f"Writing {out}...")
    df.to_csv(out, index=False, encoding="utf-8")

    print("=" * 50)
    print("SUCCESS — Custom Label Database exported.")
    print(f"Rows: {len(df)}")
    print(f"Path: {out}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Error exporting Custom Label Database:")
        print(exc)
        raise SystemExit(1)
