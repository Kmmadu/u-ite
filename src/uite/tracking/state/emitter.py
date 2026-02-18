from tracking.event_factory import EventFactory
from tracking.state.network_state import NetworkState


class NetworkEventEmitter:
    """
    Emits events based on network state transitions.
    """

    @staticmethod
    def emit(
        network_id: str,
        device_id: str,
        previous_state: NetworkState | None,
        new_state: NetworkState,
        downtime_seconds: int | None = None
    ) -> dict | None:

        # First state registration → no event
        if previous_state is None:
            return None

        # Network went DOWN
        if previous_state == NetworkState.UP and new_state == NetworkState.DOWN:
            return EventFactory.create_event(
                event_type="INTERNET_DOWN",
                device_id=device_id,
                network_id=network_id,
                description="The network transitioned from UP to DOWN."
            )

        # Network RECOVERED
        if previous_state == NetworkState.DOWN and new_state == NetworkState.UP:
            return EventFactory.create_event(
                event_type="NETWORK_RESTORED",
                device_id=device_id,
                network_id=network_id,
                description=f"Network was down for {downtime_seconds} seconds.",
                duration=downtime_seconds
            )

        return None