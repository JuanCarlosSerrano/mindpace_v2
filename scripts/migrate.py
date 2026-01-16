from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path


def main() -> None:
    db_path = os.getenv("DB_PATH", "/app/data/mindpace_dev.db")
    action = "upgrade"
    path = Path(db_path)
    if path.exists():
        conn = sqlite3.connect(str(path))
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if tables and "alembic_version" not in tables:
            action = "stamp"

    cmd = ["alembic", action, "head"]
    print(f"-> {action}: {' '.join(cmd)}")
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
