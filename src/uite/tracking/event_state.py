"""
Event State Tracking Module for U-ITE
=======================================
Maintains the previous state of network diagnostics to enable transition detection.
This simple but crucial module remembers the last known state of each monitored
attribute, allowing the event detector to identify when changes occur.

The EventState class stores:
- network_id: The last seen network identifier
- verdict: The last diagnostic verdict
- online: Whether the network was online

This state is updated after each diagnostic cycle and used by the EventDetector
to compare current and previous conditions.
"""

class EventState:
    """
    Keeps memory of previous snapshot values to detect transitions.
    
    This class maintains a simple record of the last known network state.
    It's used by the EventDetector to compare current conditions with
    previous ones, enabling detection of state changes.
    
    Attributes:
        network_id (str): Last seen network identifier
        verdict (str): Last diagnostic verdict
        online (bool): Whether the network was online in last check
    
    Example:
        >>> state = EventState()
        >>> state.update(snapshot)
        >>> if state.verdict != new_verdict:
        ...     print("Network verdict changed!")
    """

    def __init__(self):
        """
        Initialize empty state.
        
        All attributes start as None, indicating no previous state.
        The first update will populate them with actual values.
        """
        self.network_id = None
        self.verdict = None
        self.online = None

    def update(self, snapshot):
        """
        Update state with values from a new diagnostic snapshot.
        
        This method should be called after each diagnostic cycle to
        store the latest values for future comparisons.
        
        Args:
            snapshot (dict): Diagnostic snapshot containing:
                - network_id: Network identifier
                - verdict: Diagnostic verdict
                - online: Online status (derived from verdict)
        
        Example:
            >>> snapshot = {
            ...     "network_id": "net-001",
            ...     "verdict": "✅ Connected",
            ...     "online": True
            ... }
            >>> state.update(snapshot)
            >>> print(state.verdict)
            '✅ Connected'
        """
        self.network_id = snapshot.get("network_id")
        self.verdict = snapshot.get("verdict")
        self.online = snapshot.get("online")

    def has_state(self) -> bool:
        """
        Check if state has been initialized with any values.
        
        Returns:
            bool: True if at least one attribute is not None
            
        Example:
            >>> if state.has_state():
            ...     # We have previous data to compare with
            ...     pass
        """
        return any([self.network_id, self.verdict, self.online])

    def clear(self):
        """
        Reset state to initial empty values.
        
        Useful for testing or when starting fresh.
        """
        self.network_id = None
        self.verdict = None
        self.online = None

    def to_dict(self) -> dict:
        """
        Convert state to dictionary for serialization.
        
        Returns:
            dict: State attributes as a dictionary
            
        Example:
            >>> state_dict = state.to_dict()
            >>> print(state_dict)
            {'network_id': 'net-001', 'verdict': '✅ Connected', 'online': True}
        """
        return {
            "network_id": self.network_id,
            "verdict": self.verdict,
            "online": self.online
        }

    def __repr__(self) -> str:
        """
        String representation of the state.
        
        Returns:
            str: Human-readable state description
        """
        return f"EventState(network_id={self.network_id}, verdict={self.verdict}, online={self.online})"


# ============================================================================
# Usage Example
# ============================================================================

"""
How EventState is used in EventDetector:

    class EventDetector:
        def __init__(self):
            self.state = EventState()
        
        def analyze(self, snapshot):
            # Compare current with previous
            if self.state.verdict and self.state.verdict != snapshot.get("verdict"):
                # Verdict changed - generate event
                pass
            
            # Update state for next cycle
            self.state.update(snapshot)
"""


# Export public interface
__all__ = ['EventState']
