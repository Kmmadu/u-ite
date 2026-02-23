"""
Database Storage Module for U-ITE
===================================
Handles all database operations including initialization, data insertion,
and historical queries. Uses SQLite for lightweight, file-based storage
with no external dependencies.

Features:
- Automatic database initialization with schema
- OS-appropriate storage locations
- Historical data queries with date filtering
- Network-specific statistics
- Verdict summary generation
- Efficient indexing for fast queries

Database Schema:
- diagnostic_runs: Stores all network check results
- events: Stores detected network events
- network_states: Stores state history
- network_profiles: Stores network metadata
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import importlib.resources as pkg_resources
from uite.core.platform import OS

# ============================================================================
# Database Configuration
# ============================================================================

# Use OS-appropriate paths (cross-platform support)
BASE_DIR = OS.get_data_dir()          # e.g., ~/.local/share/uite/ on Linux
DB_PATH = BASE_DIR / "u_ite.db"       # Main database file
LOG_DIR = OS.get_log_dir()             # Log directory

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def init_db():
    """
    Initialize the database with the schema.
    
    Creates all necessary tables if they don't exist:
    - diagnostic_runs: Store all network check results
    - events: Store network events
    - network_states: Store state history
    - network_profiles: Store network metadata
    
    The schema is loaded from the package's schema.sql file.
    
    Returns:
        None
        
    Example:
        >>> init_db()
        # Database initialized with tables
    """
    with sqlite3.connect(DB_PATH) as conn:
        # Load schema from package (works after installation)
        from uite import storage
        schema_text = pkg_resources.read_text(storage, "schema.sql")
        conn.executescript(schema_text)


def generate_network_id(router_ip, internet_ip):
    """
    Generate a network ID from router and internet IPs.
    
    This is a legacy function - modern code should use fingerprint-based
    ID generation in core.fingerprint.
    
    Args:
        router_ip (str): Router IP address
        internet_ip (str): Internet IP address
        
    Returns:
        str: 16-character hex network ID
        
    Example:
        >>> network_id = generate_network_id("192.168.1.1", "8.8.8.8")
        >>> print(network_id)
        'a1b2c3d4e5f67890'
    """
    raw = f"{router_ip}-{internet_ip}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_run(data: dict):
    """
    Save a diagnostic run to the database.
    
    Stores the results of a single network diagnostic check.
    
    Args:
        data (dict): Diagnostic data containing:
            - network_id: Network identifier
            - router_ip: Router IP address
            - internet_ip: Internet IP checked
            - router_reachable: bool
            - internet_reachable: bool
            - dns_ok: bool
            - http_ok: bool
            - avg_latency: float or None
            - packet_loss: float or None
            - verdict: Human-readable status
            
    Returns:
        None
        
    Example:
        >>> save_run({
        ...     "network_id": "a1b2c3d4",
        ...     "router_ip": "192.168.1.1",
        ...     "internet_ip": "8.8.8.8",
        ...     "router_reachable": True,
        ...     "internet_reachable": True,
        ...     "dns_ok": True,
        ...     "http_ok": True,
        ...     "avg_latency": 15.3,
        ...     "packet_loss": 0,
        ...     "verdict": "✅ Connected"
        ... })
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO diagnostic_runs (
                timestamp,
                network_id,
                router_ip,
                internet_ip,
                router_reachable,
                internet_reachable,
                dns_ok,
                http_ok,
                avg_latency_ms,
                packet_loss_pct,
                verdict
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(),  # Current time in UTC
                data["network_id"],
                data["router_ip"],
                data["internet_ip"],
                int(data["router_reachable"]),   # Convert bool to int (0/1)
                int(data["internet_reachable"]),
                int(data["dns_ok"]),
                int(data["http_ok"]),
                data["avg_latency"],
                data["packet_loss"],
                data["verdict"],
            ),
        )


class HistoricalData:
    """
    Query historical diagnostic data from SQLite database.
    
    This class provides static methods for all data retrieval operations.
    It's designed to be used without instantiation.
    
    Example:
        >>> runs = HistoricalData.get_runs_for_last_days("a1b2c3d4", 7)
        >>> stats = HistoricalData.get_network_stats("a1b2c3d4", 30)
    """
    
    @staticmethod
    def get_runs_by_date_range(start_date, start_time, end_date, end_time, network_id=None):
        """
        Get diagnostic runs between two dates/times.
        
        Args:
            start_date: Start date in DD-MM-YYYY format
            start_time: Start time in HH:MM format
            end_date: End date in DD-MM-YYYY format
            end_time: End time in HH:MM format
            network_id: Optional network ID to filter by
        
        Returns:
            List of dictionaries, each containing:
            - timestamp: ISO format timestamp
            - network_id: Network identifier
            - verdict: Human-readable status
            - latency: Average latency in ms
            - loss: Packet loss percentage
            
        Example:
            >>> runs = HistoricalData.get_runs_by_date_range(
            ...     "01-02-2026", "00:00",
            ...     "07-02-2026", "23:59"
            ... )
        """
        # Parse dates from string format
        start_str = f"{start_date} {start_time}"
        end_str = f"{end_date} {end_time}"
        
        try:
            start_dt = datetime.strptime(start_str, "%d-%m-%Y %H:%M")
            end_dt = datetime.strptime(end_str, "%d-%m-%Y %H:%M")
        except ValueError as e:
            print(f"❌ Date parsing error: {e}")
            return []
        
        # Connect to database with row factory for dict-like access
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Build query - use datetime() for proper ISO comparison
        query = """
            SELECT 
                timestamp,
                network_id,
                verdict,
                avg_latency_ms as latency,
                packet_loss_pct as loss
            FROM diagnostic_runs
            WHERE datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
        """
        params = [start_dt.isoformat(), end_dt.isoformat()]
        
        if network_id:
            query += " AND network_id = ?"
            params.append(network_id)
        
        query += " ORDER BY timestamp ASC"
        
        # Execute query and convert rows to dicts
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    @staticmethod
    def get_runs_for_last_days(network_id, days):
        """
        Get diagnostic runs for the last N days.
        
        Convenience method for common "last N days" queries.
        
        Args:
            network_id: Network ID to filter by
            days: Number of days to look back
        
        Returns:
            List of diagnostic runs (see get_runs_by_date_range)
            
        Example:
            >>> runs = HistoricalData.get_runs_for_last_days("a1b2c3d4", 7)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for the query
        start_str = start_date.strftime("%d-%m-%Y")
        start_time = start_date.strftime("%H:%M")
        end_str = end_date.strftime("%d-%m-%Y")
        end_time = end_date.strftime("%H:%M")
        
        return HistoricalData.get_runs_by_date_range(
            start_str, start_time, end_str, end_time, network_id
        )
    
    @staticmethod
    def get_network_stats(network_id, days=30):
        """
        Get statistics for a specific network over a time period.
        
        Calculates:
        - Total number of diagnostic runs
        - Number of healthy runs (with ✅/Connected/Healthy verdict)
        - Average and maximum latency
        - Average and maximum packet loss
        
        Args:
            network_id: Network ID to analyze
            days: Number of days to look back (default: 30)
        
        Returns:
            dict: Statistics containing:
            - total_runs: int
            - healthy_runs: int
            - avg_latency: float or None
            - avg_loss: float or None
            - max_latency: float or None
            - max_loss: float or None
            
        Example:
            >>> stats = HistoricalData.get_network_stats("a1b2c3d4", 7)
            >>> print(f"Uptime: {stats['healthy_runs']/stats['total_runs']*100:.1f}%")
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN verdict LIKE '%✅%' 
                          OR verdict LIKE '%Connected%' 
                          OR verdict LIKE '%Healthy%' 
                    THEN 1 ELSE 0 END) as healthy_runs,
                AVG(avg_latency_ms) as avg_latency,
                AVG(packet_loss_pct) as avg_loss,
                MAX(avg_latency_ms) as max_latency,
                MAX(packet_loss_pct) as max_loss
            FROM diagnostic_runs
            WHERE network_id = ? 
                AND datetime(timestamp) BETWEEN datetime(?) AND datetime(?)
        """
        
        cursor = conn.execute(query, [
            network_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        ])
        result = dict(cursor.fetchone())
        conn.close()
        
        return result

    @staticmethod
    def get_verdict_summary(start_date, start_time, end_date, end_time, network_id=None):
        """
        Get a summary of verdict counts in the date range.
        
        Useful for quick overview of network health distribution.
        
        Args:
            start_date: Start date in DD-MM-YYYY format
            start_time: Start time in HH:MM format
            end_date: End date in DD-MM-YYYY format
            end_time: End time in HH:MM format
            network_id: Optional network ID to filter by
        
        Returns:
            dict: Mapping of verdict strings to counts
            
        Example:
            >>> summary = HistoricalData.get_verdict_summary(
            ...     "01-02-2026", "00:00",
            ...     "07-02-2026", "23:59"
            ... )
            >>> print(summary['✅ Connected'])
            42
        """
        runs = HistoricalData.get_runs_by_date_range(
            start_date, start_time, end_date, end_time, network_id
        )
        
        summary = {}
        for run in runs:
            verdict = run.get('verdict', 'Unknown')
            summary[verdict] = summary.get(verdict, 0) + 1
        
        return summary


# ============================================================================
# Utility Functions
# ============================================================================

def get_db_size() -> int:
    """
    Get the size of the database file in bytes.
    
    Returns:
        int: File size in bytes, or 0 if file doesn't exist
    """
    if DB_PATH.exists():
        return DB_PATH.stat().st_size
    return 0


def vacuum_db():
    """
    Vacuum the database to reclaim space and optimize performance.
    
    This rebuilds the database file, reducing fragmentation and
    recovering unused space.
    
    Returns:
        None
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("VACUUM")


def get_table_info() -> dict:
    """
    Get information about database tables.
    
    Returns:
        dict: Table names and row counts
    """
    info = {}
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            info[table] = count
    
    return info


# Export public interface
__all__ = [
    'init_db',
    'save_run',
    'HistoricalData',
    'get_db_size',
    'vacuum_db',
    'get_table_info'
]
