import sqlite3
from typing import Optional

from storage.db import DB_PATH
from tracking.state.network_state import NetworkState


class StateStore:

    @staticmethod
    def save_state(network_id: str, state: NetworkState):
        """
        Save or update network state
        """

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO network_states (network_id, state)
                VALUES (?, ?)
                ON CONFLICT(network_id)
                DO UPDATE SET state = excluded.state
                """,
                (network_id, state.value),
            )

    @staticmethod
    def get_state(network_id: str) -> Optional[NetworkState]:
        """
        Retrieve last known state
        """

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                SELECT state FROM network_states
                WHERE network_id = ?
                """,
                (network_id,),
            )

            row = cursor.fetchone()

            if row:
                return NetworkState(row[0])

            return None
