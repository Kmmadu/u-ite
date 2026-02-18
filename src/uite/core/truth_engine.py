from core.models import NetworkState, Event, Severity
from datetime import datetime
import uuid


class TruthEngine:

    def evaluate(self, diagnostic_data: dict):
        """
        Convert diagnostic run into state + event
        """

        router_ok = diagnostic_data["router_reachable"]
        internet_ok = diagnostic_data["internet_reachable"]
        dns_ok = diagnostic_data["dns_ok"]
        http_ok = diagnostic_data["http_ok"]

        network_id = diagnostic_data["network_id"]

        # -----------------------
        # Determine Network State
        # -----------------------

        if not router_ok:
            state = NetworkState.DOWN
            severity = Severity.CRITICAL
            message = "Router unreachable — possible LAN failure"

        elif router_ok and not internet_ok:
            state = NetworkState.DOWN
            severity = Severity.CRITICAL
            message = "Internet unreachable — ISP outage suspected"

        elif internet_ok and (not dns_ok or not http_ok):
            state = NetworkState.DEGRADED
            severity = Severity.WARNING
            message = "Partial service failure (DNS/HTTP)"

        else:
            state = NetworkState.UP
            severity = Severity.INFO
            message = "Network operating normally"

        # -----------------------
        # Create Event
        # -----------------------

        event = Event(
            id=str(uuid.uuid4()),
            network_id=network_id,
            device_id="truth-engine",
            severity=severity.value,
            message=message,
            timestamp=datetime.utcnow().isoformat()
        )

        return {
            "state": state,
            "event": event
        }
