from .network_info import collect_network_snapshot
from .history import save_snapshot
from ..device import get_device_id
import logging

logger = logging.getLogger("U-ITE")


def track_connection():
    """Track and store current connection info."""

    device_id = get_device_id()

    snapshot = collect_network_snapshot()
    snapshot["device_id"] = device_id

    save_snapshot(snapshot)

    logger.info("Tracking snapshot saved.")

    return snapshot
