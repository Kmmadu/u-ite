import sqlite3
from pathlib import Path
from typing import Dict, Any

from storage.db import DB_PATH


class EventStore:

    @staticmethod
    def save_event(event: Dict[str, Any]) -> None:
        """
        Persists an event into the database.
        """

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id,
                    timestamp,
                    event_type,
                    category,
                    severity,
                    device_id,
                    network_id,
                    verdict,
                    summary,
                    description,
                    duration,
                    resolved,
                    correlation_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["timestamp"],
                    event["type"],
                    event["category"],
                    event["severity"],
                    event["device_id"],
                    event["network_id"],
                    event["verdict"],
                    event["summary"],
                    event["description"],
                    event.get("duration"),
                    int(event.get("resolved", False)),
                    event.get("correlation_id"),
                ),
            )

    @staticmethod
    def get_events(network_id: str):
        """
        Retrieves events for a network.
        """

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM events
                WHERE network_id = ?
                ORDER BY timestamp DESC
                """,
                (network_id,),
            )

            return cursor.fetchall()
