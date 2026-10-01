"""Staging upload + UPDATE/INSERT/DELETE for db_update."""
from __future__ import annotations

import csv
from io import StringIO

import pandas as pd
from sqlalchemy import text

from db_update_config import (
    FORCE_MASS_DELETE,
    PRESERVE_ON_UPDATE,
    STAGING_TABLE,
    TABLE_NAME,
    q,
)


def staging_expr(col: str, db_col_types: dict[str, str]) -> str:
    src = f"s.{q(col)}"
    if db_col_types.get(col) == "jsonb":
        return (
            f"CASE WHEN {src} IS NULL OR btrim({src}) = '' "
            f"THEN NULL ELSE {src}::jsonb END"
        )
    if col in ("created_at", "updated_at"):
        return f"COALESCE({src}, NOW())"
    return src


def create_and_load_staging(conn, df: pd.DataFrame, csv_cols: list[str]) -> None:
    type_map = {
        "id": "INTEGER",
        "nc_order": "NUMERIC",
        "created_at": "TIMESTAMP",
        "updated_at": "TIMESTAMP",
        "nc_row_meta": "TEXT",
    }
    col_defs = [f"{q(col)} {type_map.get(col, 'TEXT')}" for col in csv_cols]
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


def fetch_counts(conn):
    return conn.execute(
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


def apply_sync(
    conn,
    counts,
    csv_cols: list[str],
    db_col_names: list[str],
    db_col_types: dict[str, str],
    delete_missing: bool,
) -> int:
    if counts["csv_rows"] == 0:
        print("❌ Error: CSV empty hai. Update cancel.")
        raise SystemExit(1)

    valid_ids = conn.execute(
        text(f"SELECT COUNT(*) FROM {q(STAGING_TABLE)} WHERE id IS NOT NULL")
    ).scalar()
    if valid_ids == 0:
        print("❌ Error: CSV me koi valid 'id' nahi. Galat file ho sakti hai. Update cancel.")
        raise SystemExit(1)

    if (
        delete_missing
        and counts["db_rows"]
        and counts["to_delete"] > (counts["db_rows"] * 0.5)
        and not FORCE_MASS_DELETE
    ):
        print("❌ Safety stop: CSV me 50%+ rows missing hain, isliye delete cancel.")
        print("   Agar sach me itni rows delete karni hain to FORCE_MASS_DELETE = True karo.")
        raise SystemExit(1)

    update_cols = [
        c for c in csv_cols if c not in PRESERVE_ON_UPDATE and c not in {"id", "updated_at"}
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
        insert_select = ", ".join(staging_expr(c, db_col_types) for c in insert_cols)
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
        insert_with_id_select = ", ".join(
            staging_expr(c, db_col_types) for c in insert_with_id_cols
        )
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
    if delete_missing:
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
    return deleted_count
