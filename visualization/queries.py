import sqlite3
import pandas as pd
from pathlib import Path
import sys

# ==========================================================
# [CONFIG] Project paths
# ==========================================================

# Expected project structure:
# u-ite/
# ├── u_ite/
# │   ├── layer4/
# │   │   └── data_access.py  <-- this file
# └── data/
#     └── runs.db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "runs.db"


# ==========================================================
# [LAYER 4] Data access
# ==========================================================

def fetch_all_runs_df():
    """
    Fetch all diagnostic runs from SQLite into a pandas DataFrame.

    Returns:
        pandas.DataFrame | None
    """
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found at {DB_PATH}")
        return None

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(
                """
                SELECT
                    timestamp,
                    router_reachable,
                    internet_reachable,
                    dns_ok,
                    http_ok,
                    avg_latency_ms,
                    packet_loss_pct,
                    verdict
                FROM diagnostic_runs
                ORDER BY timestamp ASC
                """,
                conn
            )

        # Convert timestamp for plotting
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Normalize column names
        df.columns = [
            "timestamp",
            "router_ok",
            "internet_ok",
            "dns_ok",
            "http_ok",
            "latency_ms",
            "loss_pct",
            "verdict"
        ]

        return df

    except Exception as e:
        print(f"[ERROR] Failed to fetch diagnostic data: {e}")
        return None


# ==========================================================
# [DEV / TEST] Dummy database generator
# ==========================================================

def create_dummy_db():
    """
    Create a dummy database for Layer 4 testing.
    Will overwrite existing DB file.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    temp_conn = sqlite3.connect(":memory:")
    cursor = temp_conn.cursor()

    cursor.execute(
        """
        CREATE TABLE diagnostic_runs (
            timestamp TEXT NOT NULL,
            router_reachable INTEGER,
            internet_reachable INTEGER,
            dns_ok INTEGER,
            http_ok INTEGER,
            avg_latency_ms REAL,
            packet_loss_pct REAL,
            verdict TEXT
        );
        """
    )

    start_time = pd.to_datetime("2026-01-01 08:00:00")
    rows = []

    for i in range(100):
        ts = (start_time + pd.Timedelta(minutes=15 * i)).isoformat()
        latency = 20 + (i % 15)
        loss = 0 if i % 12 != 0 else 5

        verdict = "Healthy"
        if loss > 0:
            verdict = "Unstable"
        if latency > 35:
            verdict = "Degraded"

        rows.append((
            ts, 1, 1, 1, 1,
            latency,
            loss,
            verdict
        ))

    cursor.executemany(
        "INSERT INTO diagnostic_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        rows
    )

    with sqlite3.connect(DB_PATH) as conn:
        temp_conn.backup(conn)

    temp_conn.close()
    print(f"[INFO] Dummy database created at {DB_PATH}")


# ==========================================================
# [CLI ENTRYPOINT] Optional dummy DB creation
# ==========================================================

if __name__ == "__main__":
    if "--dummy" in sys.argv:
        create_dummy_db()

    df = fetch_all_runs_df()
    if df is not None:
        print(df.head())
