"""Config and small helpers for db_update (NocoDB sync)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_WAREHOUSE = Path(__file__).resolve().parents[2]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared.paths import cl_csv_path  # noqa: E402

# Database credentials — do not paste into docs/chat
DB_USER = "root"
DB_PASS = "AaqY$#CGA5g3nDrx#49A"
DB_HOST = "78.46.128.21"
DB_PORT = "37005"
DB_NAME = "central_ecommerce_db"

TABLE_NAME = "Custom_Label_Database"
CSV_FILE = str(cl_csv_path())
STAGING_TABLE = "_tmp_custom_label_csv_upload"

# True: CSV se jo rows hata di hon, woh database se bhi delete ho jayengi
DELETE_ROWS_MISSING_FROM_CSV = True
# True: database change nahi hogi, sirf counts print hongi
DRY_RUN = True
# True: agar CSV me 50%+ rows missing hon to bhi delete allow karo
FORCE_MASS_DELETE = False

# NocoDB system columns — existing rows par inko CSV se overwrite nahi karna
PRESERVE_ON_UPDATE = {"created_at", "created_by", "nc_row_meta"}


def q(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def read_csv_file(path: str) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError as err:
            last_error = err
    raise last_error


def load_db_columns(conn) -> list[tuple[str, str]]:
    from sqlalchemy import text

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


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
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
    return df
