from .event_factory import EventFactory
from .event_types import EventType
from .event_state import EventState


class EventDetector:
    """Detects significant network events based on diagnostic snapshots."""

    def __init__(self, device_id: str):
        """Initializes the EventDetector with a device ID and an EventState instance.

        Args:
            device_id (str): The unique ID of the device this detector is running on.
        """
        self.device_id = device_id
        self.state = EventState()

    def analyze(self, snapshot: dict) -> list[dict]:
        """Analyzes a diagnostic snapshot and returns a list of detected events.

        Args:
            snapshot (dict): A dictionary containing the current diagnostic results.

        Returns:
            list[dict]: A list of detected event objects.
        """
        events = []

        network_id = snapshot.get("network_id")
        verdict = snapshot.get("verdict")
        # Assuming 'online' status is derived from the verdict or a specific check
        # For now, let's infer it from verdict being 'Healthy' or 'Degraded Internet'
        online = verdict in ["Healthy", "Degraded Internet"]

        # ---- Network Switch ----
        if self.state.network_id and network_id != self.state.network_id:
            events.append(
                EventFactory.create_event(
                    event_type=EventType.NETWORK_SWITCH.value,
                    device_id=self.device_id,
                    network_id=network_id,
                    description=f"Network ID changed from {self.state.network_id} to {network_id}. Verdict: {verdict}",
                    fingerprint=snapshot.get("fingerprint", {})
                )
            )

        # ---- Network Status Change (e.g., Healthy -> Degraded, Degraded -> Down) ----
        # This is a more general event that can be refined. For now, we'll use verdict changes.
        if self.state.verdict and verdict != self.state.verdict:
            # Avoid generating an event if it's just a network ID change that also changes verdict
            # This logic might need refinement based on desired event granularity
            if not (self.state.network_id and network_id != self.state.network_id):
                events.append(
                    EventFactory.create_event(
                        event_type=EventType.NETWORK_STATUS_CHANGE.value,  # ← ADD COMMA HERE
                        device_id=self.device_id,
                        network_id=network_id,
                        description=f"Diagnostic verdict changed from {self.state.verdict} to {verdict}.",
                        metrics=snapshot.get("metrics", {})
                    )
                )

        # ---- Network Lost ----
        # This assumes 'online' is a boolean derived from the snapshot
        if self.state.online is True and online is False:
            events.append(
                EventFactory.create_event(
                    event_type=EventType.INTERNET_DOWN.value,
                    device_id=self.device_id,
                    network_id=network_id,
                    description=f"Internet connectivity moved from online to offline. Current verdict: {verdict}.",
                    metrics=snapshot.get("metrics", {})
                )
            )

        # ---- Network Restored ----
        if self.state.online is False and online is True:
            events.append(
                EventFactory.create_event(
                    event_type=EventType.NETWORK_RESTORED.value,  # ← ADD COMMA HERE
                    device_id=self.device_id,
                    network_id=network_id,
                    description=f"Internet connectivity moved from offline to online. Current verdict: {verdict}.",
                    metrics=snapshot.get("metrics", {})
                )
            )

        # Update state AFTER detection for the next cycle
        self.state.update(snapshot)

        return events