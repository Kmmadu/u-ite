import sqlite3
from pathlib import Path
from datetime import datetime
import hashlib
import importlib.resources as pkg_resources

# For runtime data (writable)
BASE_DIR = Path.home() / ".uite"
DB_PATH = BASE_DIR / "data" / "u_ite.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        # Load schema from package (read-only, works after installation)
        from uite import storage
        schema_text = pkg_resources.read_text(storage, "schema.sql")
        conn.executescript(schema_text)


def generate_network_id(router_ip, internet_ip):
    raw = f"{router_ip}-{internet_ip}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_run(data: dict):
    print(f"DEBUG: Saving run for network {data.get('network_id')}")
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

class HistoricalData:
    """Query historical diagnostic data from SQLite database"""
    
    @staticmethod
    def get_runs_by_date_range(start_date, start_time, end_date, end_time, network_id=None):
        """
        Get diagnostic runs between two dates/times
        
        Args:
            start_date: Start date in DD-MM-YYYY format
            start_time: Start time in HH:MM format
            end_date: End date in DD-MM-YYYY format
            end_time: End time in HH:MM format
            network_id: Optional network ID to filter by
        
        Returns:
            List of diagnostic runs as dictionaries
        """
        # Parse dates
        start_str = f"{start_date} {start_time}"
        end_str = f"{end_date} {end_time}"
        
        try:
            start_dt = datetime.strptime(start_str, "%d-%m-%Y %H:%M")
            end_dt = datetime.strptime(end_str, "%d-%m-%Y %H:%M")
        except ValueError as e:
            print(f"❌ Date parsing error: {e}")
            return []
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        # Build query
        query = """
            SELECT 
                timestamp,
                network_id,
                verdict,
                avg_latency_ms as latency,
                packet_loss_pct as loss
            FROM diagnostic_runs
            WHERE timestamp BETWEEN ? AND ?
        """
        params = [start_dt.isoformat(), end_dt.isoformat()]
        
        if network_id:
            query += " AND network_id = ?"
            params.append(network_id)
        
        query += " ORDER BY timestamp ASC"
        
        # Execute query
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    @staticmethod
    def get_network_stats(network_id, days=30):
        """Get statistics for a specific network"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN verdict LIKE '%✅%' OR verdict LIKE '%Connected%' OR verdict LIKE '%Healthy%' THEN 1 ELSE 0 END) as healthy_runs,
                AVG(avg_latency_ms) as avg_latency,
                AVG(packet_loss_pct) as avg_loss,
                MAX(avg_latency_ms) as max_latency,
                MAX(packet_loss_pct) as max_loss
            FROM diagnostic_runs
            WHERE network_id = ? AND timestamp BETWEEN ? AND ?
        """
        
        cursor = conn.execute(query, [network_id, start_date.isoformat(), end_date.isoformat()])
        result = dict(cursor.fetchone())
        conn.close()
        
        return result

    @staticmethod
    def get_verdict_summary(start_date, start_time, end_date, end_time, network_id=None):
        """Get a summary of verdicts in the date range"""
        runs = HistoricalData.get_runs_by_date_range(
            start_date, start_time, end_date, end_time, network_id
        )
        
        summary = {}
        for run in runs:
            verdict = run.get('verdict', 'Unknown')
            summary[verdict] = summary.get(verdict, 0) + 1
        
        return summary
