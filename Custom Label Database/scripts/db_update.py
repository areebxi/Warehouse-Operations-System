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
import sys
import csv
from io import StringIO

import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Database Credentials
DB_USER = "root"
DB_PASS = "AaqY$#CGA5g3nDrx#49A"
DB_HOST = "78.46.128.21"
DB_PORT = "37005"
DB_NAME = "central_ecommerce_db"

# 2. CSV / table (db_export.py jaisi file)
TABLE_NAME = "Custom_Label_Database"
CSV_FILE = "Custom_Label_Database.csv"
STAGING_TABLE = "_tmp_custom_label_csv_upload"

# 3. Options
# True: CSV se jo rows hata di hon, woh database se bhi delete ho jayengi
DELETE_ROWS_MISSING_FROM_CSV = True
# True: database change nahi hogi, sirf counts print hongi
DRY_RUN = True
# True: agar CSV me 50%+ rows missing hon to bhi delete allow karo
FORCE_MASS_DELETE = False

# NocoDB system columns — existing rows par inko CSV se overwrite nahi karna
PRESERVE_ON_UPDATE = {"created_at", "created_by", "nc_row_meta"}


def q(name):
    return '"' + str(name).replace('"', '""') + '"'


def read_csv_file(path):
    last_error = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError as err:
            last_error = err
    raise last_error


def load_db_columns(conn):
    rows = conn.execute(
        text(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :t
            ORDER BY ordinal_position
            """
        ),
        {"t": TABLE_NAME},
    )
    return [(row[0], row[1]) for row in rows]


try:
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: '{CSV_FILE}' nahi mili. Pehle python db_export.py chalao.")
        raise SystemExit(1)

    print(f"⏳ Reading CSV file: {CSV_FILE}...")
    df = read_csv_file(CSV_FILE)
    df.columns = df.columns.str.strip()

    if "id" not in df.columns:
        print("❌ Error: CSV me 'id' column nahi hai. Original exported file use karo.")
        raise SystemExit(1)

    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    if "nc_order" in df.columns:
        df["nc_order"] = pd.to_numeric(df["nc_order"], errors="coerce")

    obj_cols = df.select_dtypes(include=["object"]).columns
    if len(obj_cols):
        df[obj_cols] = df[obj_cols].replace(r"^\s*$", pd.NA, regex=True)

    id_non_null = df.loc[df["id"].notna(), "id"]
    duplicate_ids = int(id_non_null.duplicated().sum())
    if duplicate_ids:
        print(f"⚠️ Duplicate id rows mili hain ({duplicate_ids}). Last row rakh rahe hain.")
        has_id = df["id"].notna()
        df = pd.concat(
            [
                df.loc[has_id].drop_duplicates(subset=["id"], keep="last"),
                df.loc[~has_id],
            ],
            ignore_index=True,
        )

    encoded_pass = quote_plus(DB_PASS)
    db_url = f"postgresql://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(db_url)

    print(f"⏳ Connecting to PostgreSQL...")
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

        def staging_expr(col):
            src = f"s.{q(col)}"
            if db_col_types.get(col) == "jsonb":
                return (
                    f"CASE WHEN {src} IS NULL OR btrim({src}) = '' "
                    f"THEN NULL ELSE {src}::jsonb END"
                )
            if col in ("created_at", "updated_at"):
                return f"COALESCE({src}, NOW())"
            return src

        # Staging table: CSV columns, quoted mixed-case names
        type_map = {
            "id": "INTEGER",
            "nc_order": "NUMERIC",
            "created_at": "TIMESTAMP",
            "updated_at": "TIMESTAMP",
            "nc_row_meta": "TEXT",
        }
        col_defs = []
        for col in csv_cols:
            col_defs.append(f"{q(col)} {type_map.get(col, 'TEXT')}")

        conn.execute(text(f"DROP TABLE IF EXISTS {q(STAGING_TABLE)}"))
        conn.execute(text(f"CREATE TABLE {q(STAGING_TABLE)} ({', '.join(col_defs)})"))

        print(f"⏳ Uploading {len(df)} CSV rows to staging table...")
        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False, na_rep="\\N", quoting=csv.QUOTE_MINIMAL)
        buffer.seek(0)

        copy_sql = (
            f"COPY {q(STAGING_TABLE)} ({', '.join(q(c) for c in csv_cols)}) "
            "FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
        )
        raw_conn = conn.connection.dbapi_connection
        with raw_conn.cursor() as cur:
            cur.copy_expert(copy_sql, buffer)

        counts = conn.execute(
            text(
                f"""
                SELECT
                    (SELECT COUNT(*) FROM {q(TABLE_NAME)}) AS db_rows,
                    (SELECT COUNT(*) FROM {q(STAGING_TABLE)}) AS csv_rows,
                    (SELECT COUNT(*) FROM {q(STAGING_TABLE)} s
                     WHERE s.id IS NOT NULL
                       AND EXISTS (SELECT 1 FROM {q(TABLE_NAME)} t WHERE t.id = s.id)
                    ) AS to_update,
                    (SELECT COUNT(*) FROM {q(STAGING_TABLE)} s
                     WHERE s.id IS NULL
                        OR NOT EXISTS (SELECT 1 FROM {q(TABLE_NAME)} t WHERE t.id = s.id)
                    ) AS to_insert,
                    (SELECT COUNT(*) FROM {q(TABLE_NAME)} t
                     WHERE NOT EXISTS (
                         SELECT 1 FROM {q(STAGING_TABLE)} s
                         WHERE s.id IS NOT NULL AND s.id = t.id
                     )
                    ) AS to_delete
                """
            )
        ).mappings().one()

        print("\n" + "=" * 50)
        print(f"📊 Database rows : {counts['db_rows']}")
        print(f"📄 CSV rows      : {counts['csv_rows']}")
        print(f"✏️  Will UPDATE  : {counts['to_update']}")
        print(f"➕ Will INSERT   : {counts['to_insert']}")
        if DELETE_ROWS_MISSING_FROM_CSV:
            print(f"🗑️  Will DELETE  : {counts['to_delete']}")
        else:
            print(f"🗑️  Will DELETE  : 0 (DELETE_ROWS_MISSING_FROM_CSV=False)")
        print("=" * 50)

        if DRY_RUN:
            conn.execute(text(f"DROP TABLE IF EXISTS {q(STAGING_TABLE)}"))
            print("\nℹ️ DRY_RUN=True — database me koi change nahi hua.")
            raise SystemExit(0)

        if counts["csv_rows"] == 0:
            print("❌ Error: CSV empty hai. Update cancel.")
            raise SystemExit(1)

        valid_ids = conn.execute(text(f"SELECT COUNT(*) FROM {q(STAGING_TABLE)} WHERE id IS NOT NULL")).scalar()
        if valid_ids == 0:
            print("❌ Error: CSV me koi valid 'id' nahi. Galat file ho sakti hai. Update cancel.")
            raise SystemExit(1)

        if (
            DELETE_ROWS_MISSING_FROM_CSV
            and counts["db_rows"]
            and counts["to_delete"] > (counts["db_rows"] * 0.5)
            and not FORCE_MASS_DELETE
        ):
            print("❌ Safety stop: CSV me 50%+ rows missing hain, isliye delete cancel.")
            print("   Agar sach me itni rows delete karni hain to FORCE_MASS_DELETE = True karo.")
            raise SystemExit(1)

        update_cols = [
            c
            for c in csv_cols
            if c not in PRESERVE_ON_UPDATE and c not in {"id", "updated_at"}
        ]
        set_parts = [f"{q(c)} = s.{q(c)}" for c in update_cols]
        if "updated_at" in db_col_names:
            set_parts.append(f"{q('updated_at')} = NOW()")

        if set_parts:
            print(f"⏳ Updating {counts['to_update']} existing rows...")
            conn.execute(
                text(
                    f"""
                    UPDATE {q(TABLE_NAME)} AS t
                    SET {', '.join(set_parts)}
                    FROM {q(STAGING_TABLE)} AS s
                    WHERE t.id = s.id
                    """
                )
            )

        insert_cols = [c for c in csv_cols if c != "id"]
        print(f"⏳ Inserting {counts['to_insert']} new rows...")
        if insert_cols:
            insert_select = ", ".join(staging_expr(c) for c in insert_cols)
            conn.execute(
                text(
                    f"""
                    INSERT INTO {q(TABLE_NAME)} ({', '.join(q(c) for c in insert_cols)})
                    SELECT {insert_select}
                    FROM {q(STAGING_TABLE)} s
                    WHERE s.id IS NULL
                    """
                )
            )
            insert_with_id_cols = ["id"] + insert_cols
            insert_with_id_select = ", ".join(staging_expr(c) for c in insert_with_id_cols)
            conn.execute(
                text(
                    f"""
                    INSERT INTO {q(TABLE_NAME)} ({', '.join(q(c) for c in insert_with_id_cols)})
                    SELECT {insert_with_id_select}
                    FROM {q(STAGING_TABLE)} s
                    WHERE s.id IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM {q(TABLE_NAME)} t WHERE t.id = s.id
                      )
                    """
                )
            )

        deleted_count = 0
        if DELETE_ROWS_MISSING_FROM_CSV:
            print(f"⏳ Deleting {counts['to_delete']} rows missing from CSV...")
            result = conn.execute(
                text(
                    f"""
                    DELETE FROM {q(TABLE_NAME)} t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM {q(STAGING_TABLE)} s
                        WHERE s.id IS NOT NULL AND s.id = t.id
                    )
                    """
                )
            )
            deleted_count = result.rowcount

        conn.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{q(TABLE_NAME)}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {q(TABLE_NAME)}), 1),
                    true
                )
                """
            )
        )
        conn.execute(text(f"DROP TABLE IF EXISTS {q(STAGING_TABLE)}"))

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
