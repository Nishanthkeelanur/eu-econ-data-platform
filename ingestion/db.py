"""Cloud SQL access via the Cloud SQL Python Connector.

Connections go through Google's connector (TLS to the instance's proxy
port), so no authorized networks are needed. Normal operation uses IAM
authentication - passwordless, identity comes from ADC locally or the
service account in CI. The password path exists only for the one-off
"postgres" admin user used by migrations.
"""

import os

from google.cloud.sql.connector import Connector

from ingestion import config


def connect(user: str | None = None, password: str | None = None):
    """Open a pg8000 connection; returns (connector, connection).

    Caller must close both. Without a password, connects with IAM auth
    as `user` (default: DB_IAM_USER env var).
    """
    connector = Connector()
    if password:
        conn = connector.connect(
            config.SQL_CONNECTION_NAME, "pg8000",
            user=user, password=password, db=config.SQL_DATABASE,
        )
    else:
        user = user or os.environ["DB_IAM_USER"]
        conn = connector.connect(
            config.SQL_CONNECTION_NAME, "pg8000",
            user=user, db=config.SQL_DATABASE, enable_iam_auth=True,
        )
    return connector, conn


def upsert(conn, table: str, rows: list[dict], key_cols: list[str]) -> int:
    """Idempotent bulk upsert: INSERT ... ON CONFLICT (keys) DO UPDATE.

    Re-running a load never duplicates rows; changed values (e.g. revised
    statistics) overwrite the old ones and refresh loaded_at.
    """
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in key_cols)
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(key_cols)}) "
        f"DO UPDATE SET {updates}, loaded_at = now()"
    )
    cur = conn.cursor()
    cur.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
    conn.commit()
    return len(rows)
