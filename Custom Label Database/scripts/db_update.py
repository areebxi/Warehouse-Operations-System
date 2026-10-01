"""
Custom_Label_Database ko CSV se wapas update karne ka script.

Workflow:
  1. python db_export.py
  2. Custom_Label_Database.csv Excel mein edit karke save karo
  3. python db_update.py

id column mat hatao. Nayi row ke liye id khali chhod do.
CSV se row delete karoge to database se bhi delete hogi
(DELETE_ROWS_MISSING_FROM_CSV = True).
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

_HERE = Path(__file__).resolve().parent
_WAREHOUSE = _HERE.parents[1]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from db_update_config import (  # noqa: E402
    CSV_FILE,
    DB_HOST,
    DB_NAME,
    DB_PASS,
    DB_PORT,
    DB_USER,
    DELETE_ROWS_MISSING_FROM_CSV,
    DRY_RUN,
    STAGING_TABLE,
    TABLE_NAME,
    load_db_columns,
    prepare_dataframe,
    q,
    read_csv_file,
)
from db_update_sync import apply_sync, create_and_load_staging, fetch_counts  # noqa: E402

try:
    print(f"⏳ Reading CSV file: {CSV_FILE}...")
    df = prepare_dataframe(read_csv_file(CSV_FILE))

    encoded_pass = quote_plus(DB_PASS)
    db_url = f"postgresql://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)

    print("⏳ Connecting to PostgreSQL...")
    with engine.begin() as conn:
        db_cols = load_db_columns(conn)
        if not db_cols:
            print(f"❌ Error: table {q(TABLE_NAME)} nahi mili.")
            raise SystemExit(1)

        db_col_names = [name for name, _ in db_cols]
        db_col_types = {name: dtype for name, dtype in db_cols}
        csv_cols = [c for c in df.columns if c in db_col_names]
        extra_cols = [c for c in df.columns if c not in db_col_names]
        if extra_cols:
            print(f"ℹ️ CSV ki extra columns skip: {', '.join(extra_cols)}")

        df = df[csv_cols].copy()
        create_and_load_staging(conn, df, csv_cols)
        counts = fetch_counts(conn)
        print(
            f"📊 Staging={counts['csv_rows']} DB={counts['db_rows']} "
            f"update={counts['to_update']} insert={counts['to_insert']} "
            f"delete={counts['to_delete']}"
        )

        if DRY_RUN:
            print("DRY RUN — no writes")
            conn.execute(text(f"DROP TABLE IF EXISTS {q(STAGING_TABLE)}"))
            raise SystemExit(0)

        deleted_count = apply_sync(
            conn,
            counts=counts,
            csv_cols=csv_cols,
            db_col_names=db_col_names,
            db_col_types=db_col_types,
            delete_missing=DELETE_ROWS_MISSING_FROM_CSV,
        )
        final_count = conn.execute(text(f"SELECT COUNT(*) FROM {q(TABLE_NAME)}")).scalar()

    print("\n" + "=" * 50)
    print("✅ SUCCESS! Custom_Label_Database CSV se update ho gayi.")
    print(f"✏️  Updated : {counts['to_update']}")
    print(f"➕ Inserted : {counts['to_insert']}")
    print(f"🗑️  Deleted  : {deleted_count}")
    print(f"📊 Table rows now: {final_count}")
    print("=" * 50)
    print("ℹ️ NocoDB me page refresh karo taake naya data dikhe.")

except SystemExit:
    raise
except Exception as e:
    print("❌ Error updating table from CSV:")
    print(e)
