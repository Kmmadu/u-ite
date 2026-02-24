"""
Network Event Emitter Module for U-ITE
=======================================
Emits events based on network state transitions. This module is responsible
for creating appropriate events when the network state changes (UP→DOWN,
DOWN→UP, etc.).

The emitter works with the NetworkStateEngine to generate events that are
then stored in the database for historical analysis and alerting.
"""

from typing import Optional, Dict, Union

from uite.tracking.event_factory import EventFactory
from uite.tracking.state.network_state import NetworkState


class NetworkEventEmitter:
    """
    Emits events based on network state transitions.
    
    This class is used by the NetworkStateEngine to generate events when
    meaningful network state changes occur. It handles:
    - First-time state registration (no event)
    - UP → DOWN transitions (internet down events)
    - DOWN → UP transitions (recovery events with downtime)
    """

    @staticmethod
    def emit(
        network_id: str,
        device_id: str,
        previous_state: Optional[NetworkState],
        new_state: NetworkState,
        downtime_seconds: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Emit an event based on network state transition.
        
        Args:
            network_id (str): Identifier of the affected network
            device_id (str): Identifier of the device detecting the change
            previous_state (Optional[NetworkState]): Previous network state (None if first registration)
            new_state (NetworkState): New network state
            downtime_seconds (Optional[int]): Duration of downtime for recovery events
            
        Returns:
            Optional[Dict]: Event dictionary if transition triggered an event, None otherwise
        """
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
