from datetime import datetime, timezone
from typing import Dict, Optional

from tracking.state.network_state import NetworkState
from tracking.state.transitions import is_valid_transition
from tracking.state.emitter import NetworkEventEmitter
from storage.state_store import StateStore


class NetworkStateEngine:
    """
    Tracks network states and emits events when valid state transitions occur.
    Persists state to database for recovery after restart.
    """

    def __init__(self):
        # In-memory cache (fast access)
        self._states: Dict[str, NetworkState] = {}

        # Tracks when network went DOWN
        self._down_since: Dict[str, datetime] = {}

    def update_state(self, network_id: str, new_state: NetworkState) -> Dict:
        """
        Updates network state and emits events when transitions occur.
        """

        # ---- Load state from memory first ----
        previous_state: Optional[NetworkState] = self._states.get(network_id)

        # ---- If not in memory, try loading from DB ----
        if previous_state is None:
            previous_state = StateStore.get_state(network_id)

            # Cache DB state in memory
            if previous_state:
                self._states[network_id] = previous_state

        # ---- First time state assignment ----
        if previous_state is None:
            self._states[network_id] = new_state
            StateStore.save_state(network_id, new_state)

            if new_state == NetworkState.DOWN:
                self._down_since[network_id] = datetime.now(timezone.utc)

            return {
                "transitioned": True,
                "previous_state": None,
                "new_state": new_state,
                "downtime_seconds": None,
            }

        # ---- Ignore invalid transitions ----
        if not is_valid_transition(previous_state, new_state):
            return {
                "transitioned": False,
                "previous_state": previous_state,
                "new_state": previous_state,
                "downtime_seconds": None,
            }

        downtime_seconds = None

        # ---- DOWN → UP recovery ----
        if previous_state == NetworkState.DOWN and new_state == NetworkState.UP:
            down_time = self._down_since.pop(network_id, None)

            if down_time:
                downtime_seconds = int(
                    (datetime.now(timezone.utc) - down_time).total_seconds()
                )

        # ---- UP → DOWN ----
        if new_state == NetworkState.DOWN:
            self._down_since[network_id] = datetime.now(timezone.utc)

        # ---- Persist + Cache new state ----
        self._states[network_id] = new_state
        StateStore.save_state(network_id, new_state)

        # ---- Emit Event ----
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
