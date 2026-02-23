"""
Network State Engine Module for U-ITE
=======================================
Tracks network states, validates transitions, and emits events. This is the
heart of the state management system, maintaining both in-memory cache and
persistent storage.

Features:
- In-memory cache for fast access
- Database persistence for recovery after restarts
- Validates state transitions
- Tracks downtime durations
- Emits events for significant transitions
- Handles first-time registration

State Machine:
    UP ←→ DOWN (valid transitions)
    UP ←→ DEGRADED (valid transitions)
    DOWN ←→ RECOVERING (valid transitions)
    Other transitions are invalid and ignored

Downtime Tracking:
    - Records when a network goes DOWN
    - Calculates duration when it comes back UP
    - Stores downtime in events and database
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from uite.tracking.state.network_state import NetworkState
from uite.tracking.state.transitions import is_valid_transition
from uite.tracking.state.emitter import NetworkEventEmitter
from uite.storage.state_store import StateStore


class NetworkStateEngine:
    """
    Tracks network states and emits events when valid state transitions occur.
    Persists state to database for recovery after restart.
    
    This engine maintains two data structures:
    - _states: In-memory cache of current states (fast access)
    - _down_since: Tracks when each network went DOWN (for downtime calculation)
    
    Example:
        >>> engine = NetworkStateEngine()
        >>> result = engine.update_state("net-001", NetworkState.UP)
        >>> print(result['transitioned'])
        True
        >>> result = engine.update_state("net-001", NetworkState.DOWN)
        >>> # Later, when network recovers:
        >>> result = engine.update_state("net-001", NetworkState.UP)
        >>> print(result['downtime_seconds'])
        125
    """

    def __init__(self):
        """
        Initialize the state engine with empty caches.
        
        - _states: In-memory cache for fast state lookup
        - _down_since: Tracks when each network entered DOWN state
        """
        # In-memory cache (fast access)
        self._states: Dict[str, NetworkState] = {}

        # Tracks when network went DOWN (for downtime calculation)
        self._down_since: Dict[str, datetime] = {}

    def update_state(self, network_id: str, new_state: NetworkState) -> Dict:
        """
        Update network state and emit events when transitions occur.
        
        This is the main entry point for state changes. It:
        1. Loads current state from cache or database
        2. Handles first-time registration
        3. Validates transitions
        4. Calculates downtime for recovery
        5. Persists new state
        6. Emits events
        
        Args:
            network_id (str): Network identifier
            new_state (NetworkState): New state to set
        
        Returns:
            dict: Result containing:
                - transitioned (bool): Whether state actually changed
                - previous_state (NetworkState or None): Previous state
                - new_state (NetworkState): New state
                - downtime_seconds (int or None): Downtime if recovering
                - event (dict or None): Emitted event if any
        
        Example:
            >>> result = engine.update_state("net-001", NetworkState.DOWN)
            >>> if result['transitioned']:
            ...     print(f"Network went from {result['previous_state']} to DOWN")
        """

        # ====================================================================
        # Load current state
        # First check memory cache, then database
        # ====================================================================
        previous_state: Optional[NetworkState] = self._states.get(network_id)

        # If not in memory, try loading from database
        if previous_state is None:
            previous_state = StateStore.get_state(network_id)

            # Cache DB state in memory for future fast access
            if previous_state:
                self._states[network_id] = previous_state

        # ====================================================================
        # First time state assignment
        # This network has never been seen before
        # ====================================================================
        if previous_state is None:
            self._states[network_id] = new_state
            StateStore.save_state(network_id, new_state)

            # If starting in DOWN state, start tracking downtime
            if new_state == NetworkState.DOWN:
                self._down_since[network_id] = datetime.now(timezone.utc)

            return {
                "transitioned": True,
                "previous_state": None,
                "new_state": new_state,
                "downtime_seconds": None,
            }

        # ====================================================================
        # Validate transition
        # Some transitions are not allowed (e.g., UP → RECOVERING)
        # ====================================================================
        if not is_valid_transition(previous_state, new_state):
            return {
                "transitioned": False,
                "previous_state": previous_state,
                "new_state": previous_state,
                "downtime_seconds": None,
            }

        # ====================================================================
        # Calculate downtime for recovery (DOWN → UP)
        # ====================================================================
        downtime_seconds = None
        if previous_state == NetworkState.DOWN and new_state == NetworkState.UP:
            down_time = self._down_since.pop(network_id, None)

            if down_time:
                downtime_seconds = int(
                    (datetime.now(timezone.utc) - down_time).total_seconds()
                )

        # ====================================================================
        # Track when network goes DOWN (start timing)
        # ====================================================================
        if new_state == NetworkState.DOWN:
            self._down_since[network_id] = datetime.now(timezone.utc)

        # ====================================================================
        # Persist new state to database and update cache
        # ====================================================================
        self._states[network_id] = new_state
        StateStore.save_state(network_id, new_state, downtime_seconds)

        # ====================================================================
        # Emit event for significant transitions
        # ====================================================================
        event = NetworkEventEmitter.emit(
            network_id=network_id,
            device_id="gateway-001",  # TODO: Make device_id configurable
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


# ============================================================================
# Utility Functions
# ============================================================================

def format_state_summary(state_result: Dict) -> str:
    """
    Format a state update result for display.
    
    Args:
        state_result: Result dict from update_state()
    
    Returns:
        str: Human-readable summary
    """
    if not state_result['transitioned']:
        return f"No change (already {state_result['new_state'].value})"
    
    if state_result['previous_state'] is None:
        return f"Initial state: {state_result['new_state'].value}"
    
    if state_result['downtime_seconds']:
        return (f"Recovered from {state_result['previous_state'].value} to "
                f"{state_result['new_state'].value} after "
                f"{state_result['downtime_seconds']}s downtime")
    
    return (f"Transition: {state_result['previous_state'].value} → "
            f"{state_result['new_state'].value}")


# Export public interface
__all__ = ['NetworkStateEngine', 'format_state_summary']
