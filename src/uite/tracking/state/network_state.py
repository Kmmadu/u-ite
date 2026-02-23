"""
Network State Enumeration Module for U-ITE
===========================================
Defines the possible states a network can be in and provides validation
utilities. This module serves as the single source of truth for network
health states throughout the application.

States:
    - UP: Network is fully operational
    - DEGRADED: Network is up but experiencing issues
    - DOWN: Network is completely down/unreachable
    - RECOVERING: Network is in the process of coming back up

The states are designed to represent the complete lifecycle of network
connectivity, from healthy operation through various failure modes to
recovery.
"""

from enum import Enum


class NetworkState(str, Enum):
    """
    Represents the current health state of a monitored network.
    
    This enum defines all possible states a network can be in. Each state
    is a string value for easy serialization and database storage.
    
    State Descriptions:
        UP:          Network is fully operational with no issues detected.
                     All connectivity tests pass.
        
        DEGRADED:    Network is up but experiencing performance issues.
                     This could include high latency, packet loss, or
                     intermittent connectivity problems.
        
        DOWN:        Network is completely down/unreachable. No connectivity
                     to router, internet, or any services.
        
        RECOVERING:  Network is in the process of coming back up after being
                     down. This is a transitional state used to prevent
                     alert storms during flapping connections.
    
    Usage:
        >>> from uite.tracking.state import NetworkState
        >>> current_state = NetworkState.UP
        >>> if current_state == NetworkState.DOWN:
        ...     alert_admin()
        >>> print(current_state.value)
        'UP'
    """

    UP = "UP"
    DEGRADED = "DEGRADED"
    DOWN = "DOWN"
    RECOVERING = "RECOVERING"


def is_valid_network_state(value) -> bool:
    """
    Validate if a given value represents a valid NetworkState.
    
    This function accepts either NetworkState enum members or their
    string representations, making it flexible for different use cases.
    
    Args:
        value: The value to validate. Can be:
            - A NetworkState enum member
            - A string (case-insensitive) like "UP", "down", "Degraded"
            - Any other type (returns False)
    
    Returns:
        bool: True if the value represents a valid network state,
              False otherwise.
    
    Examples:
        >>> is_valid_network_state(NetworkState.UP)
        True
        
        >>> is_valid_network_state("DOWN")
        True
        
        >>> is_valid_network_state("down")  # Case-insensitive
        True
        
        >>> is_valid_network_state("UNKNOWN")
        False
        
        >>> is_valid_network_state(123)
        False
    
    Notes:
        - String comparison is case-insensitive
        - Leading/trailing whitespace is not stripped
        - Only exact matches to state names are accepted
    """
    # Case 1: Direct enum member
    if isinstance(value, NetworkState):
        return True

    # Case 2: String representation (case-insensitive)
    if isinstance(value, str):
        return value.upper() in NetworkState.__members__

    # Case 3: Any other type
    return False


# ============================================================================
# Additional Utility Functions
# ============================================================================

def get_all_states() -> list:
    """
    Get a list of all possible network states.
    
    Returns:
        list: List of all NetworkState enum members
        
    Example:
        >>> from uite.tracking.state import get_all_states
        >>> states = get_all_states()
        >>> for state in states:
        ...     print(state.value)
        'UP'
        'DEGRADED'
        'DOWN'
        'RECOVERING'
    """
    return list(NetworkState)


def get_state_description(state: NetworkState) -> str:
    """
    Get a human-readable description of a network state.
    
    Args:
        state (NetworkState): The state to describe
        
    Returns:
        str: Description of what the state means
        
    Example:
        >>> from uite.tracking.state import get_state_description
        >>> print(get_state_description(NetworkState.DEGRADED))
        'Network is up but experiencing performance issues'
    """
    descriptions = {
        NetworkState.UP: "Network is fully operational with no issues detected",
        NetworkState.DEGRADED: "Network is up but experiencing performance issues",
        NetworkState.DOWN: "Network is completely down/unreachable",
        NetworkState.RECOVERING: "Network is in the process of coming back up",
    }
    return descriptions.get(state, "Unknown state")


def get_state_severity(state: NetworkState) -> str:
    """
    Get the severity level associated with a network state.
    
    Useful for alerting and prioritization.
    
    Args:
        state (NetworkState): The state to check
        
    Returns:
        str: Severity level ("INFO", "WARNING", "CRITICAL")
        
    Example:
        >>> from uite.tracking.state import get_state_severity
        >>> print(get_state_severity(NetworkState.DOWN))
        'CRITICAL'
    """
    severity_map = {
        NetworkState.UP: "INFO",
        NetworkState.DEGRADED: "WARNING",
        NetworkState.DOWN: "CRITICAL",
        NetworkState.RECOVERING: "INFO",
    }
    return severity_map.get(state, "UNKNOWN")


def get_state_emoji(state: NetworkState) -> str:
    """
    Get an emoji representation of a network state.
    
    Useful for CLI output and notifications.
    
    Args:
        state (NetworkState): The state to represent
        
    Returns:
        str: Emoji representing the state
        
    Example:
        >>> from uite.tracking.state import get_state_emoji
        >>> print(get_state_emoji(NetworkState.UP))
        '✅'
    """
    emoji_map = {
        NetworkState.UP: "✅",
        NetworkState.DEGRADED: "⚠️",
        NetworkState.DOWN: "🔴",
        NetworkState.RECOVERING: "🔄",
    }
    return emoji_map.get(state, "❓")


# Export public interface
__all__ = [
    'NetworkState',
    'is_valid_network_state',
    'get_all_states',
    'get_state_description',
    'get_state_severity',
    'get_state_emoji'
]
