"""
U-ITE State Management Package
================================
A comprehensive state management system for tracking network states,
validating transitions, and emitting events.

This package provides a complete state machine implementation for network
monitoring, including:
- State definitions (UP, DOWN, DEGRADED, RECOVERING)
- Transition validation rules
- State persistence
- Event emission for significant changes
- Downtime tracking and calculation

Package Structure:
    - engine.py: Core state engine with caching and persistence
    - network_state.py: NetworkState enum definitions
    - transitions.py: Transition validation logic
    - emitter.py: Event emission for state changes
    - __init__.py: Package exports and documentation

Usage:
    >>> from uite.tracking.state import NetworkStateEngine, NetworkState
    >>> engine = NetworkStateEngine()
    >>> result = engine.update_state("net-001", NetworkState.UP)
"""

from .engine import NetworkStateEngine
from .network_state import NetworkState
from .transitions import is_valid_transition
from .emitter import NetworkEventEmitter


# ============================================================================
# Package Exports
# ============================================================================

# Define what gets imported with "from uite.tracking.state import *"
__all__ = [
    # Core engine for state management
    "NetworkStateEngine",
    
    # State enum for network status
    "NetworkState",
    
    # Transition validation function
    "is_valid_transition",
    
    # Event emitter for state changes
    "NetworkEventEmitter",
]


# ============================================================================
# Package Metadata
# ============================================================================

__version__ = "1.0.0"
__author__ = "U-ITE Team"
__description__ = "Network state management and transition system"


# ============================================================================
# Module Documentation
# ============================================================================

def get_state_info() -> dict:
    """
    Get information about available states and transitions.
    
    Returns:
        dict: State information including:
            - states: List of all possible states
            - transitions: Description of valid transitions
            
    Example:
        >>> from uite.tracking.state import get_state_info
        >>> info = get_state_info()
        >>> print(info['states'])
        ['UP', 'DOWN', 'DEGRADED', 'RECOVERING']
    """
    return {
        "states": [state.value for state in NetworkState],
        "transitions": (
            "Valid transitions are defined in transitions.py. "
            "Generally, networks can transition between UP, DOWN, and DEGRADED "
            "states, with RECOVERING as an intermediate state."
        ),
        "version": __version__
    }


def quick_start_example() -> str:
    """
    Provide a quick start code example.
    
    Returns:
        str: Example code showing basic usage
        
    Example:
        >>> from uite.tracking.state import quick_start_example
        >>> print(quick_start_example())
    """
    return '''
# Quick Start Example for State Management

from uite.tracking.state import NetworkStateEngine, NetworkState

# Create engine instance
engine = NetworkStateEngine()

# Update network state
result = engine.update_state("office-net", NetworkState.UP)
print(f"State updated: {result['transitioned']}")

# When network goes down
result = engine.update_state("office-net", NetworkState.DOWN)
print(f"Downtime started")

# After recovery (with automatic downtime calculation)
import time
time.sleep(60)  # Simulate 60 seconds of downtime
result = engine.update_state("office-net", NetworkState.UP)
print(f"Downtime: {result['downtime_seconds']} seconds")
'''


# ============================================================================
# Convenience Functions
# ============================================================================

def create_state_engine() -> NetworkStateEngine:
    """
    Create and return a new NetworkStateEngine instance.
    
    This is a convenience factory function for creating state engines.
    
    Returns:
        NetworkStateEngine: A new state engine instance
        
    Example:
        >>> from uite.tracking.state import create_state_engine
        >>> engine = create_state_engine()
    """
    return NetworkStateEngine()


def is_valid_state(value: str) -> bool:
    """
    Check if a string value represents a valid network state.
    
    Args:
        value (str): String to check
        
    Returns:
        bool: True if value is a valid NetworkState
        
    Example:
        >>> from uite.tracking.state import is_valid_state
        >>> is_valid_state("UP")
        True
        >>> is_valid_state("INVALID")
        False
    """
    try:
        NetworkState(value)
        return True
    except ValueError:
        return False


# Export convenience functions
__all__.extend([
    'get_state_info',
    'quick_start_example',
    'create_state_engine',
    'is_valid_state'
])
