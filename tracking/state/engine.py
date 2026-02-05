from datetime import datetime, timezone
from typing import Dict, Optional

from tracking.state.network_state import NetworkState
from tracking.state.transitions import is_valid_transition
from tracking.state.emitter import NetworkEventEmitter


class NetworkStateEngine:
    """
    Tracks network states and emits events when valid state transitions occur.
    """

    def __init__(self):
        # Stores current state per network_id
        self._states: Dict[str, NetworkState] = {}

        # Stores when a network went DOWN (for downtime calculation)
        self._down_since: Dict[str, datetime] = {}

    def update_state(self, network_id: str, new_state: NetworkState) -> Dict:
        """
        Updates the state of a network and emits an event if a valid transition occurs.
        """

        previous_state: Optional[NetworkState] = self._states.get(network_id)

        # First state assignment (no transition validation needed)
        if previous_state is None:
            self._states[network_id] = new_state

            if new_state == NetworkState.DOWN:
                self._down_since[network_id] = datetime.now(timezone.utc)

            return {
                "transitioned": True,
                "previous_state": None,
                "new_state": new_state,
                "downtime_seconds": None,
            }

        # Ignore invalid transitions
        if not is_valid_transition(previous_state, new_state):
            return {
                "transitioned": False,
                "previous_state": previous_state,
                "new_state": previous_state,
                "downtime_seconds": None,
            }

        downtime_seconds = None

        # Handle DOWN → UP recovery
        if previous_state == NetworkState.DOWN and new_state == NetworkState.UP:
            down_time = self._down_since.pop(network_id, None)
            if down_time:
                downtime_seconds = int(
                    (datetime.now(timezone.utc) - down_time).total_seconds()
                )

        # Handle UP → DOWN
        if new_state == NetworkState.DOWN:
            self._down_since[network_id] = datetime.now(timezone.utc)

        # Persist new state
        self._states[network_id] = new_state

        # Emit network event
        event = NetworkEventEmitter.emit(
            network_id=network_id,
            device_id="gateway-001",
            previous_state=previous_state,
            new_state=new_state,
            downtime_seconds=downtime_seconds,
        )

        return {
            "transitioned": True,
            "previous_state": previous_state,
            "new_state": new_state,
            "downtime_seconds": downtime_seconds,
            "event": event,
        }
