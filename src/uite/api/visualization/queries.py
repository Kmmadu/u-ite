import sqlite3
import pandas as pd
from pathlib import Path
import sys

# ==========================================================
# [CONFIG] Project paths
# ==========================================================

# visualization/queries.py
# Project root = u-ite/
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "u_ite.db"

# ==========================================================
# [LAYER 4] Data access
# ==========================================================

def fetch_all_runs_df():
    """
    Fetch all diagnostic runs from SQLite into a pandas DataFrame.
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
                    router_reachable   AS router_ok,
                    internet_reachable AS internet_ok,
                    dns_ok,
                    http_ok,
                    avg_latency        AS latency_ms,
                    packet_loss        AS loss_pct,
                    verdict
                FROM runs
                ORDER BY timestamp ASC
                """,
                conn
            )

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    except Exception as e:
        print(f"[ERROR] Failed to fetch diagnostic data: {e}")
        return None


# ==========================================================
# [DEV ONLY] Optional test entry
# ==========================================================

if __name__ == "__main__":
    df = fetch_all_runs_df()
    if df is not None:
        print(df.head())
