"""Apply schema.sql to Cloud SQL as the postgres admin user.

Usage (password comes from the environment, never from a file in git):
    ADMIN_DB_PASSWORD=... python -m ingestion.migrate
"""

import os
from pathlib import Path

from ingestion import db


def main() -> None:
    password = os.environ["ADMIN_DB_PASSWORD"]
    sql = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    # Drop comment lines first: pg8000 statements are split on ";", and a
    # semicolon inside a comment would otherwise cut a statement in half.
    sql = "\n".join(
        line for line in sql.splitlines() if not line.lstrip().startswith("--")
    )

    connector, conn = db.connect(user="postgres", password=password)
    try:
        cur = conn.cursor()
        # pg8000 can't execute multi-statement strings; run them one by one.
        for statement in sql.split(";"):
            if statement.strip():
                cur.execute(statement)
        conn.commit()
        print("Schema applied successfully")
    finally:
        conn.close()
        connector.close()


if __name__ == "__main__":
    main()
