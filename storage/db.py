import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "u_ite.db"
SCHEMA_PATH = BASE_DIR / "u_ite" / "schema.sql"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())


def generate_network_id(router_ip, internet_ip):
    raw = f"{router_ip}-{internet_ip}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_run(data: dict):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO runs (
                timestamp,
                network_id,
                router_ip,
                internet_ip,
                router_reachable,
                internet_reachable,
                dns_ok,
                http_ok,
                avg_latency,
                packet_loss,
                verdict
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),
                data["network_id"],
                data["router_ip"],
                data["internet_ip"],
                int(data["router_reachable"]),
                int(data["internet_reachable"]),
                int(data["dns_ok"]),
                int(data["http_ok"]),
                data["avg_latency"],
                data["packet_loss"],
                data["verdict"],
            ),
        )
