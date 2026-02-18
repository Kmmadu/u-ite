import sqlite3
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone

from uite.storage.db import DB_PATH

if TYPE_CHECKING:
    from uite.tracking.state.network_state import NetworkState


class StateStore:

    @staticmethod
    def save_state(
        network_id: str,
        state: 'NetworkState',
        downtime_seconds: Optional[float] = None,
    ):
        """
        Persist a network state change as historical record
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
                    state.value,
                    datetime.now(timezone.utc).isoformat(),
                    downtime_seconds,
                ),
            )

    @staticmethod
    def get_state_history(network_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve full history of states for a network
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
        Retrieve only the most recent state for a network
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
        Alias for get_latest_state - maintains backward compatibility
        """
        return StateStore.get_latest_state(network_id)

    @staticmethod
    def get_all_network_states() -> Dict[str, 'NetworkState']:
        """
        Get latest state for all networks
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
        Remove old state entries to prevent database from growing too large
        """
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