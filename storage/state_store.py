from datetime import datetime
from storage.db import get_connection


class StateStore:

    def save_state(self, network_id, state):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO network_states(network_id, state, last_updated)
        VALUES (?, ?, ?)
        ON CONFLICT(network_id)
        DO UPDATE SET
            state = excluded.state,
            last_updated = excluded.last_updated
        """, (
            network_id,
            state,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_state(self, network_id):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM network_states WHERE network_id=?
        """, (network_id,))

        row = cursor.fetchone()
        conn.close()

        return row
