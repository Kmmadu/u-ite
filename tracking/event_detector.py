from .events import create_event
from .event_types import EventType
from .event_state import EventState


class EventDetector:

    def __init__(self):
        self.state = EventState()

    def analyze(self, snapshot):
        events = []

        network_id = snapshot.get("network_id")
        verdict = snapshot.get("verdict")
        online = snapshot.get("online")

        # ---- Network Switch ----
        if self.state.network_id and network_id != self.state.network_id:
            events.append(
                create_event(
                    EventType.NETWORK_SWITCH,
                    {
                        "from": self.state.network_id,
                        "to": network_id
                    }
                )
            )

        # ---- Network Status Change ----
        if self.state.verdict and verdict != self.state.verdict:
            events.append(
                create_event(
                    EventType.NETWORK_STATUS_CHANGE,
                    {
                        "from": self.state.verdict,
                        "to": verdict
                    }
                )
            )

        # ---- Network Lost ----
        if self.state.online is True and online is False:
            events.append(
                create_event(
                    EventType.NETWORK_LOST,
                    {"network_id": self.state.network_id}
                )
            )

        # ---- Network Restored ----
        if self.state.online is False and online is True:
            events.append(
                create_event(
                    EventType.NETWORK_RESTORED,
                    {"network_id": network_id}
                )
            )

        # Update state AFTER detection
        self.state.update(snapshot)

        return events
