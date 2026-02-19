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
    verdict TEXT,
    -- Add provider info columns (must be at the end for ALTER to work)
    provider_name TEXT,
    network_name TEXT,
    network_tags TEXT
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

-- ===============================
-- Network Profiles (Network Identity)
-- ===============================
CREATE TABLE IF NOT EXISTS network_profiles (
    network_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT,
    tags TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    notes TEXT,
    total_runs INTEGER DEFAULT 0,
    avg_latency REAL,
    avg_loss REAL,
    uptime_percentage REAL
);

-- ===============================
-- Indexes for Performance
-- ===============================

-- Index for diagnostic runs by network and time
CREATE INDEX IF NOT EXISTS idx_diagnostic_runs_network 
ON diagnostic_runs(network_id, timestamp);

-- Index for network states by network and time
CREATE INDEX IF NOT EXISTS idx_network_states_network_id 
ON network_states(network_id, timestamp DESC);

-- Index for events by network
CREATE INDEX IF NOT EXISTS idx_events_network 
ON events(network_id, timestamp);

-- Index for events by type
CREATE INDEX IF NOT EXISTS idx_events_type 
ON events(event_type);