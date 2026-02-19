"""Historical data query module for U-ITE"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Database path - adjust based on your structure
DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "u_ite.db"

class HistoricalData:
    """Query historical diagnostic data"""
    
    @staticmethod
    def _parse_datetime(date_str: str, time_str: str) -> str:
        """Parse date and time strings to ISO format"""
        # Try different date formats
        for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"]:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Invalid date format: {date_str}")
        
        # Parse time
        try:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")
        
        # Combine
        dt = datetime.combine(date_obj, time_obj)
        return dt.isoformat()
    
    @staticmethod
    def get_runs_by_date_range(
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        network_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get diagnostic runs between two dates/times
        """
        start_iso = HistoricalData._parse_datetime(start_date, start_time)
        end_iso = HistoricalData._parse_datetime(end_date, end_time)
        
        if not DB_PATH.exists():
            print(f"Database not found at {DB_PATH}")
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        
        query = """
            SELECT 
                timestamp,
                network_id,
                verdict,
                router_reachable,
                internet_reachable,
                dns_ok,
                http_ok,
                avg_latency_ms as latency,
                packet_loss_pct as loss
            FROM diagnostic_runs
            WHERE timestamp BETWEEN ? AND ?
        """
        params = [start_iso, end_iso]
        
        if network_id:
            query += " AND network_id = ?"
            params.append(network_id)
        
        query += " ORDER BY timestamp ASC"
        
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
