CREATE TABLE IF NOT EXISTS diagnostic_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    network_id TEXT NOT NULL,
    router_ip TEXT,
    internet_ip TEXT,
    router_reachable INTEGER,
    internet_reachable INTEGER,
    dns_ok INTEGER,
    http_ok INTEGER,
    avg_latency_ms REAL,
    packet_loss_pct REAL,
    verdict TEXT
);
