import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib

DB_PATH = Path("data/u_ite.db")


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                network_id TEXT NOT NULL,
                router_ip TEXT,
                internet_ip TEXT,
                router_reachable INTEGER,
                internet_reachable INTEGER,
                dns_ok INTEGER,
                http_ok INTEGER,
                avg_latency REAL,
                packet_loss INTEGER,
                verdict TEXT
            )
        """)


def generate_network_id(router_ip, internet_ip):
    raw = f"{router_ip}-{internet_ip}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def save_run(run):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO runs (
                timestamp, network_id, router_ip, internet_ip,
                router_reachable, internet_reachable,
                dns_ok, http_ok, avg_latency, packet_loss, verdict
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            run["network_id"],
            run["router_ip"],
            run["internet_ip"],
            int(run["router_reachable"]),
            int(run["internet_reachable"]),
            int(run["dns_ok"]),
            int(run["http_ok"]),
            run["avg_latency"],
            run["packet_loss"],
            run["verdict"],
        ))
