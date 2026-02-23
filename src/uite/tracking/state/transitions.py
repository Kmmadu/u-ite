"""
Network State Transition Rules for U-ITE
=========================================
Defines which state transitions are allowed in the network state machine.
This module serves as the single source of truth for state transition rules,
ensuring that the system only allows valid state changes.

The transition rules are designed to model realistic network behavior:
- UP can go to DEGRADED or DOWN (deterioration)
- DEGRADED can improve to UP or worsen to DOWN
- DOWN can only go to RECOVERING (can't go directly to UP)
- RECOVERING can go to UP (success) or back to DEGRADED (partial recovery)

This prevents invalid transitions like UP → RECOVERING or DOWN → DEGRADED,
which wouldn't make sense in real network scenarios.
"""

from uite.tracking.state.network_state import NetworkState


# ============================================================================
# Transition Rules
# ============================================================================

# Defines valid state transitions using a dictionary where:
# - Keys are source states
# - Values are sets of allowed destination states
#
# This structure allows O(1) lookup for transition validation.
VALID_TRANSITIONS = {
    # From UP state - can only get worse
    NetworkState.UP: {
        NetworkState.DEGRADED,  # Performance degradation
        NetworkState.DOWN,      # Complete failure
    },

    # From DEGRADED state - can improve or get worse
    NetworkState.DEGRADED: {
        NetworkState.UP,        # Full recovery
        NetworkState.DOWN,      # Complete failure
    },

    # From DOWN state - must go through RECOVERING first
    NetworkState.DOWN: {
        NetworkState.RECOVERING,  # Starting to come back
        NetworkState.UP,          # Direct recovery (allowed as shortcut)
    },

    # From RECOVERING state - can succeed or fail partially
    NetworkState.RECOVERING: {
        NetworkState.UP,          # Full recovery
        NetworkState.DEGRADED,    # Partial recovery (still having issues)
    },
}


def is_valid_transition(current_state: NetworkState, new_state: NetworkState) -> bool:
    """
    Check if a transition between two network states is allowed.
    
    This function validates state changes according to the rules defined
    in VALID_TRANSITIONS. It allows:
    - Staying in the same state (always valid)
    - Moving to any state defined in the transition rules
    
    Args:
        current_state (NetworkState): The current network state
        new_state (NetworkState): The proposed new state
    
    Returns:
        bool: True if the transition is allowed, False otherwise
    
    Examples:
        >>> from uite.tracking.state import NetworkState
        >>> is_valid_transition(NetworkState.UP, NetworkState.DOWN)
        True   # UP can go to DOWN
        
        >>> is_valid_transition(NetworkState.DOWN, NetworkState.UP)
        True   # DOWN can go to UP (shortcut allowed)
        
        >>> is_valid_transition(NetworkState.UP, NetworkState.RECOVERING)
        False  # UP cannot go to RECOVERING
        
        >>> is_valid_transition(NetworkState.DOWN, NetworkState.DEGRADED)
        False  # DOWN cannot go directly to DEGRADED
        
        >>> # Same state is always allowed
        >>> is_valid_transition(NetworkState.UP, NetworkState.UP)
        True
    
    Notes:
        - Staying in the same state is always allowed (no transition needed)
        - The transition rules are designed to model realistic network behavior
        - DOWN → UP is allowed as a shortcut for DOWN → RECOVERING → UP
    """
    # Case 1: Same state - always allowed (no actual transition)
    if current_state == new_state:
        return True

    # Case 2: Check if the transition is defined in our rules
    # Get the set of allowed destinations for the current state
    allowed_transitions = VALID_TRANSITIONS.get(current_state, set())
    
    # Return True if the new state is in the allowed set
    return new_state in allowed_transitions


# ============================================================================
# Utility Functions
# ============================================================================

def get_allowed_transitions(state: NetworkState) -> set:
    """
    Get all states that can be transitioned to from a given state.
    
    Args:
        state (NetworkState): The source state
    
    Returns:
        set: Set of allowed destination states (including itself)
    
    Example:
        >>> from uite.tracking.state import NetworkState
        >>> allowed = get_allowed_transitions(NetworkState.UP)
        >>> print([s.value for s in allowed])
        ['UP', 'DEGRADED', 'DOWN']
    """
    allowed = VALID_TRANSITIONS.get(state, set()).copy()
    allowed.add(state)  # Self-transition is always allowed
    return allowed


def get_transition_graph() -> dict:
    """
    Get a complete graph of all allowed transitions.
    
    Returns:
        dict: Mapping from source state to list of destination states
    
    Example:
        >>> graph = get_transition_graph()
        >>> for source, dests in graph.items():
        ...     print(f"{source.value} → {[d.value for d in dests]}")
    """
    return {
        source: list(dests) for source, dests in VALID_TRANSITIONS.items()
    }


def can_transition_directly(current_state: NetworkState, new_state: NetworkState) -> bool:
    """
    Check if a direct transition is allowed (excluding self-transition).
    
    This is a convenience wrapper around is_valid_transition that
    explicitly excludes the self-transition case.
    
    Args:
        current_state: Current state
        new_state: Desired new state
    
    Returns:
        bool: True if a direct (different) transition is allowed
    """
    if current_state == new_state:
        return False
    return is_valid_transition(current_state, new_state)


# ============================================================================
# Transition Matrix Documentation
# ============================================================================

TRANSITION_MATRIX = """
Network State Transition Matrix
================================

Current → New      | Valid? | Explanation
-------------------|--------|------------
UP → UP            | ✓ Yes  | No change
UP → DEGRADED      | ✓ Yes  | Performance degradation
UP → DOWN          | ✓ Yes  | Complete failure
UP → RECOVERING    | ✗ No   | Can't recover without being down

DEGRADED → UP      | ✓ Yes  | Full recovery
DEGRADED → DEGRADED| ✓ Yes  | No change
DEGRADED → DOWN    | ✓ Yes  | Worsening to failure
DEGRADED → RECOVERING| ✗ No | Recovering implies was down

DOWN → UP          | ✓ Yes  | Quick recovery (shortcut)
DOWN → DEGRADED    | ✗ No   | Can't go directly to degraded
DOWN → DOWN        | ✓ Yes  | No change
DOWN → RECOVERING  | ✓ Yes  | Starting to recover

RECOVERING → UP    | ✓ Yes  | Full recovery
RECOVERING → DEGRADED| ✓ Yes| Partial recovery
RECOVERING → DOWN  | ✗ No   | Would go back to DOWN directly
RECOVERING → RECOVERING| ✓ Yes| No change
"""


# Export public interface
__all__ = [
    'is_valid_transition',
    'get_allowed_transitions',
    'get_transition_graph',
    'can_transition_directly',
    'VALID_TRANSITIONS',
    'TRANSITION_MATRIX',
]
