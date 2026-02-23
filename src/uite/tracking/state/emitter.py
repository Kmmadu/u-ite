"""
Network Event Emitter Module for U-ITE
=======================================
Generates domain events when network state transitions occur. This module
acts as the bridge between the state engine and the event system, creating
meaningful events that can be stored, alerted on, or displayed to users.

Features:
- Emits events only for meaningful state transitions
- Handles first-time registration (no event)
- Creates appropriate events for DOWN and RECOVERY
- Includes downtime duration in recovery events
- Uses EventFactory for consistent event creation

Transition Rules:
- First state registration → No event (initial state)
- UP → DOWN → Emit INTERNET_DOWN event
- DOWN → UP → Emit NETWORK_RESTORED event with duration
- Other transitions → No event (handled by event detector)
"""

from uite.tracking.event_factory import EventFactory
from uite.tracking.state.network_state import NetworkState


class NetworkEventEmitter:
    """
    Emits events based on network state transitions.
    
    This class is responsible for creating domain events when significant
    network state changes occur. It works in conjunction with the
    NetworkStateEngine to generate events that can be persisted and alerted.
    
    The emitter follows these rules:
    - No event on first state registration (initial state)
    - Event on UP → DOWN (internet loss)
    - Event on DOWN → UP (recovery, includes downtime)
    - Other transitions are ignored (handled by event detector)
    
    Example:
        >>> event = NetworkEventEmitter.emit(
        ...     network_id="net-001",
        ...     device_id="gateway-001",
        ...     previous_state=NetworkState.UP,
        ...     new_state=NetworkState.DOWN,
        ...     downtime_seconds=None
        ... )
    """

    @staticmethod
    def emit(
        network_id: str,
        device_id: str,
        previous_state: NetworkState | None,
        new_state: NetworkState,
        downtime_seconds: int | None = None
    ) -> dict | None:
        """
        Emit an event for a network state transition.
        
        Evaluates the state transition and creates an appropriate event
        if the transition is significant.
        
        Args:
            network_id (str): Identifier of the affected network
            device_id (str): Identifier of the device detecting the change
            previous_state (NetworkState | None): Previous network state,
                                                 None for first registration
            new_state (NetworkState): New network state
            downtime_seconds (int | None): Duration of downtime for recovery
                                          events (DOWN→UP only)
        
        Returns:
            dict | None: Event dictionary if transition triggered an event,
                        None otherwise
        
        Event Types:
            - "INTERNET_DOWN": When network goes from UP to DOWN
            - "NETWORK_RESTORED": When network recovers from DOWN to UP
        
        Example:
            >>> # DOWN event
            >>> event = NetworkEventEmitter.emit(
            ...     "net-001", "gw-001",
            ...     NetworkState.UP, NetworkState.DOWN
            ... )
            >>> print(event['type'])
            'INTERNET_DOWN'
            
            >>> # Recovery event with downtime
            >>> event = NetworkEventEmitter.emit(
            ...     "net-001", "gw-001",
            ...     NetworkState.DOWN, NetworkState.UP,
            ...     downtime_seconds=125
            ... )
            >>> print(event['type'])
            'NETWORK_RESTORED'
            >>> print(event['duration'])
            125
        """
        # Case 1: First time registration - no event needed
        # This is just establishing initial state
        if previous_state is None:
            return None

        # Case 2: Network went DOWN (UP → DOWN)
        # This is a critical event - internet connectivity lost
        if previous_state == NetworkState.UP and new_state == NetworkState.DOWN:
            return EventFactory.create_event(
                event_type="INTERNET_DOWN",
                device_id=device_id,
                network_id=network_id,
                description="The network transitioned from UP to DOWN."
            )

        # Case 3: Network recovered (DOWN → UP)
        # This is an informational event, includes downtime duration
        if previous_state == NetworkState.DOWN and new_state == NetworkState.UP:
            return EventFactory.create_event(
                event_type="NETWORK_RESTORED",
                device_id=device_id,
                network_id=network_id,
                description=f"Network was down for {downtime_seconds} seconds.",
                duration=downtime_seconds
            )

        # Case 4: Other transitions (e.g., UP→DEGRADED, DEGRADED→DOWN)
        # These are handled by the event detector for more granular events
        return None


# ============================================================================
# Usage Example
# ============================================================================
"""
# In NetworkStateEngine.update_state():

# After validating transition and calculating downtime
event = NetworkEventEmitter.emit(
    network_id=network_id,
    device_id=device_id,
    previous_state=previous_state,
    new_state=new_state,
    downtime_seconds=downtime_seconds
)

if event:
    # Store event, send alerts, etc.
    save_event(event)
"""
