"""
Network State Storage Module for U-ITE
=======================================
Manages persistent storage of network state transitions and history.
This module tracks the state of each network over time, enabling historical
analysis of network behavior and downtime calculations.

Features:
- Store every state change with timestamps
- Track downtime durations for DOWN→UP transitions
- Query full state history for any network
- Get latest state for quick access
- Clean up old entries automatically
- Avoid circular imports with TYPE_CHECKING

Database Schema:
- id: Auto-incrementing primary key
- network_id: Network identifier
- state: Current state (UP/DOWN/DEGRADED/etc.)
- timestamp: When the state was recorded
- downtime_seconds: Duration of last downtime (if applicable)
"""

import sqlite3
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone

from uite.storage.db import DB_PATH

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from uite.tracking.state.network_state import NetworkState


class StateStore:
    """
    Persistent storage for network state history.
    
    This class provides static methods for all state storage operations.
    It uses the main database connection from db.py and handles the
    network_states table.
    
    Example:
        >>> from uite.tracking.state.network_state import NetworkState
        >>> StateStore.save_state("net-001", NetworkState.DOWN, 120)
        >>> history = StateStore.get_state_history("net-001", limit=10)
        >>> latest = StateStore.get_latest_state("net-001")
    """
    
    @staticmethod
    def save_state(
        network_id: str,
        state: 'NetworkState',
        downtime_seconds: Optional[float] = None,
    ):
        """
        Persist a network state change as historical record.
        
        This method stores every state transition, allowing full history
        reconstruction. For DOWN→UP transitions, the downtime duration
        should be provided.
        
        Args:
            network_id (str): Network identifier
            state (NetworkState): New state (UP/DOWN/DEGRADED/etc.)
            downtime_seconds (float, optional): Duration of last downtime
                                               (for UP after DOWN)
        
        Returns:
            None
            
        Example:
            >>> StateStore.save_state("net-001", NetworkState.DOWN)
            >>> # Later, after recovery:
            >>> StateStore.save_state("net-001", NetworkState.UP, downtime_seconds=125)
        """
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO network_states (
                    network_id,
                    state,
                    timestamp,
                    downtime_seconds
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    network_id,
                    state.value,  # Store the string value, not the enum
                    datetime.now(timezone.utc).isoformat(),
                    downtime_seconds,
                ),
            )

    @staticmethod
    def get_state_history(network_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve full history of states for a network.
        
        Returns states in reverse chronological order (most recent first).
        
        Args:
            network_id (str): Network to query
            limit (int): Maximum number of records to return (default: 100)
        
        Returns:
            List[dict]: List of state records, each containing:
                - id: Database record ID
                - state: State string (e.g., "UP", "DOWN")
                - timestamp: ISO format timestamp
                - downtime_seconds: Downtime duration (if applicable)
        
        Example:
            >>> history = StateStore.get_state_history("net-001", limit=5)
            >>> for entry in history:
            ...     print(f"{entry['timestamp']}: {entry['state']}")
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                SELECT id, state, timestamp, downtime_seconds
                FROM network_states
                WHERE network_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (network_id, limit)
            )
            
            return [
                {
                    "id": row[0],
                    "state": row[1],
                    "timestamp": row[2],
                    "downtime_seconds": row[3]
                }
                for row in cursor.fetchall()
            ]

    @staticmethod
    def get_latest_state(network_id: str) -> Optional['NetworkState']:
        """
        Retrieve only the most recent state for a network.
        
        This is useful for quickly checking current network status.
        
        Args:
            network_id (str): Network to query
        
        Returns:
            NetworkState or None: Most recent state, or None if no records
        
        Example:
            >>> current = StateStore.get_latest_state("net-001")
            >>> if current == NetworkState.UP:
            ...     print("Network is up")
        """
        # Import here to avoid circular import
        from uite.tracking.state.network_state import NetworkState
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                SELECT state
                FROM network_states
                WHERE network_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (network_id,)
            )
            
            row = cursor.fetchone()
            return NetworkState(row[0]) if row else None

    @staticmethod
    def get_state(network_id: str) -> Optional['NetworkState']:
        """
        Alias for get_latest_state - maintains backward compatibility.
        
        Args:
            network_id (str): Network to query
        
        Returns:
            NetworkState or None: Most recent state
        """
        return StateStore.get_latest_state(network_id)

    @staticmethod
    def get_all_network_states() -> Dict[str, 'NetworkState']:
        """
        Get the latest state for all networks.
        
        Returns a dictionary mapping network IDs to their most recent state.
        Useful for dashboard displays and overview reports.
        
        Returns:
            dict: Mapping of network_id -> NetworkState
        
        Example:
            >>> all_states = StateStore.get_all_network_states()
            >>> for net_id, state in all_states.items():
            ...     print(f"{net_id}: {state}")
        """
        # Import here to avoid circular import
        from uite.tracking.state.network_state import NetworkState
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT network_id, state
                FROM network_states ns1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM network_states ns2
                    WHERE ns1.network_id = ns2.network_id
                )
                """
            )
            
            return {row[0]: NetworkState(row[1]) for row in cursor.fetchall()}

    @staticmethod
    def cleanup_old_entries(days_to_keep: int = 30) -> int:
        """
        Remove old state entries to prevent database from growing too large.
        
        Deletes entries older than the specified number of days.
        This is typically called periodically to manage database size.
        
        Args:
            days_to_keep (int): Number of days of history to retain (default: 30)
        
        Returns:
            int: Number of deleted records
        
        Example:
            >>> deleted = StateStore.cleanup_old_entries(days_to_keep=90)
            >>> print(f"Cleaned up {deleted} old state records")
        """
        # Calculate cutoff date (beginning of the day)
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff_date = cutoff_date.replace(
            day=cutoff_date.day - days_to_keep
        )
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                DELETE FROM network_states
                WHERE timestamp < ?
                """,
                (cutoff_date.isoformat(),)
            )
            
            return conn.total_changes


# ============================================================================
# Utility Functions
# ============================================================================

def get_state_summary(network_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Get a summary of state changes over a time period.
    
    Args:
        network_id (str): Network to analyze
        days (int): Number of days to look back
    
    Returns:
        dict: Summary containing:
            - total_changes: Number of state changes
            - uptime_percentage: Percentage of time in UP state
            - downtime_seconds: Total downtime
            - state_counts: Count of each state
    """
    from datetime import datetime, timedelta
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        
        # Get all state changes in the period
        cursor = conn.execute(
            """
            SELECT state, downtime_seconds
            FROM network_states
            WHERE network_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
            """,
            (network_id, start_date.isoformat(), end_date.isoformat())
        )
        
        records = cursor.fetchall()
        
        if not records:
            return {
                'total_changes': 0,
                'uptime_percentage': 0,
                'downtime_seconds': 0,
                'state_counts': {}
            }
        
        # Calculate statistics
        state_counts = {}
        total_downtime = 0
        
        for record in records:
            state = record['state']
            state_counts[state] = state_counts.get(state, 0) + 1
            
            if record['downtime_seconds']:
                total_downtime += record['downtime_seconds']
        
        # Estimate uptime percentage based on state counts
        # This is approximate - for precise uptime, use diagnostic_runs
        up_count = state_counts.get('UP', 0)
        total_changes = len(records)
        uptime_pct = (up_count / total_changes) * 100 if total_changes > 0 else 0
        
        return {
            'total_changes': total_changes,
            'uptime_percentage': uptime_pct,
            'downtime_seconds': total_downtime,
            'state_counts': state_counts
        }


# Export public interface
__all__ = [
    'StateStore',
    'get_state_summary'
]
