-- ===============================
-- Diagnostic Runs (Historical Checks)
-- ===============================
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

-- ===============================
-- Event Storage (Event History)
-- ===============================
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    network_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    summary TEXT,
    description TEXT,
    duration REAL,
    resolved INTEGER,
    correlation_id TEXT
);

-- ===============================
-- Network State Storage (Full History)
-- ===============================
CREATE TABLE IF NOT EXISTS network_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id TEXT NOT NULL,
    state TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    downtime_seconds REAL
);

-- Index for faster queries by network and time
CREATE INDEX IF NOT EXISTS idx_network_states_network_id 
ON network_states(network_id, timestamp DESC);
