"""
U-ITE Tracking Package - Event detection and management
=========================================================
This package provides comprehensive event detection and management capabilities
for network monitoring. It handles the entire event lifecycle from detection
through storage.

The tracking package is organized into several specialized modules:
- event_detector.py: Core detection logic with debouncing
- event_factory.py: Event creation and validation
- event_state.py: State tracking for transition detection
- event_types.py: Event type definitions
- category.py: Event category definitions
- severity.py: Severity level definitions
- state/: State machine for network conditions

Note: Event persistence is handled by the storage package, but we expose
EventStore here for convenience.
"""

# Import public interfaces from submodules
from .event_detector import EventDetector
from .category import Category
from .event_types import EventType
from .event_factory import EventFactory
from .event_state import EventState
from .severity import Severity

# Import from storage package
from uite.storage.event_store import EventStore

# Import subpackages
from . import state  # State machine subpackage

# ============================================================================
# Public API
# ============================================================================
# These are the classes and functions that are available when users do:
#   from uite.tracking import *
# or access via the package directly:
#   import uite.tracking
#   uite.tracking.EventDetector
# ============================================================================

__all__ = [
    # Core detection classes
    "EventDetector",      # Main event detection logic
    "EventState",         # State tracking for transitions
    
    # Event creation and management
    "EventFactory",       # Factory for creating validated events
    "EventStore",         # SQLite event storage (from storage package)
    
    # Enums and types
    "Category",           # Event categories (CONNECTIVITY, PERFORMANCE, etc.)
    "EventType",          # Event types (INTERNET_DOWN, HIGH_LATENCY, etc.)
    "Severity",           # Severity levels (INFO, WARNING, CRITICAL)
    
    # Subpackages
    "state",              # State machine subpackage (NetworkStateEngine, etc.)
]
