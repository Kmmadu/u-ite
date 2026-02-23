"""
Event Factory Module for U-ITE
================================
Provides a centralized factory for creating and validating network events.
This module ensures all events conform to the expected schema and have valid
metadata before they are stored or processed.

Features:
- Centralized event definitions (single source of truth)
- Automatic UUID generation for event IDs
- Timestamp generation with millisecond precision
- Comprehensive validation of all event fields
- Type-safe event creation with dataclasses
- Extensible event type registry
"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

from uite.tracking.event_types import EventType, is_valid_event_type
from uite.tracking.category import Category, is_valid_category
from uite.tracking.severity import Severity, is_valid_severity


# ============================================================================
# Custom Exceptions
# ============================================================================

class EventValidationError(Exception):
    """
    Raised when event validation fails.
    
    This can happen for several reasons:
    - Invalid event type
    - Missing event definition
    - Invalid category or severity
    - Missing required fields
    """
    pass


# ============================================================================
# Event Schema
# ============================================================================

@dataclass
class Event:
    """
    Immutable event data structure.
    
    This dataclass defines the complete schema for all U-ITE events.
    Fields are automatically generated where possible:
    - event_id: Random UUID
    - timestamp: Current UTC time with milliseconds
    
    All events must include:
    - type: Event type from EventType enum
    - category: Event category from Category enum
    - severity: Severity level from Severity enum
    - device_id: Source device identifier
    - network_id: Affected network
    - verdict: Current network verdict
    - summary: Short human-readable summary
    - description: Detailed description
    
    Optional fields:
    - metrics: Performance metrics (latency, loss, etc.)
    - fingerprint: Network fingerprint data
    - duration: How long the event lasted
    - resolved: Whether the issue is resolved
    - correlation_id: Group related events
    
    Example:
        >>> event = Event(
        ...     type="INTERNET_DOWN",
        ...     category="CONNECTIVITY",
        ...     severity="CRITICAL",
        ...     device_id="dev-001",
        ...     network_id="net-123",
        ...     verdict="Network unreachable",
        ...     summary="Internet connection lost",
        ...     description="No internet connectivity"
        ... )
    """
    
    # Auto-generated fields
    event_id: str = field(init=False)
    timestamp: str = field(init=False)

    # Required fields
    type: str
    category: str
    severity: str
    device_id: str
    network_id: str
    verdict: str
    summary: str
    description: str

    # Optional fields
    metrics: Dict[str, Any] = field(default_factory=dict)
    fingerprint: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None
    resolved: bool = False
    correlation_id: Optional[str] = None

    def __post_init__(self):
        """
        Generate auto-filled fields after initialization.
        
        This method runs automatically after the dataclass is created:
        - event_id: Random UUID4 for uniqueness
        - timestamp: Current UTC time with millisecond precision
        """
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ============================================================================
# Event Factory
# ============================================================================

class EventFactory:
    """
    Factory for creating validated event objects.
    
    This class serves as the single source of truth for event definitions.
    Each event type has a predefined set of metadata that ensures consistency
    across all event creation.
    
    The factory handles:
    - Event type validation
    - Metadata lookup from definitions
    - Category and severity validation
    - Required field validation
    - Event object creation
    
    Example:
        >>> event = EventFactory.create_event(
        ...     event_type="INTERNET_DOWN",
        ...     device_id="dev-001",
        ...     network_id="net-123",
        ...     description="Internet connection lost"
        ... )
    """

    # ========================================================================
    # Event Definitions
    # Single source of truth for all event metadata
    # ========================================================================
    EVENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {

        # --- Connectivity Loss ---
        EventType.INTERNET_DOWN.value: {
            "category": Category.CONNECTIVITY.value,
            "severity": Severity.CRITICAL.value,
            "summary": "Internet connection lost",
            "verdict": "Network unreachable",
            "resolved": False,
        },

        # --- Connectivity Restored ---
        EventType.NETWORK_RESTORED.value: {
            "category": Category.CONNECTIVITY.value,
            "severity": Severity.INFO.value,
            "summary": "Internet connection restored",
            "verdict": "Connectivity recovered",
            "resolved": True,
        },

        # --- Network Switch ---
        EventType.NETWORK_SWITCH.value: {
            "category": Category.CONNECTIVITY.value,
            "severity": Severity.INFO.value,
            "summary": "Network switched",
            "verdict": "Network changed",
            "resolved": False,
        },

        # --- Status Change ---
        "NETWORK_STATUS_CHANGE": {
            "category": Category.PERFORMANCE.value,
            "severity": Severity.WARNING.value,
            "summary": "Network status changed",
            "verdict": "Network condition changed",
            "resolved": False,
        },
    }

    @staticmethod
    def create_event(
        event_type: str,
        device_id: str,
        network_id: str,
        description: str,
        metrics: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create and validate a new event.
        
        This is the main entry point for event creation. It performs
        comprehensive validation and returns a complete event dictionary
        ready for storage.
        
        Args:
            event_type (str): Type of event (from EventType enum)
            device_id (str): Source device identifier
            network_id (str): Affected network identifier
            description (str): Detailed event description
            metrics (dict, optional): Performance metrics
            fingerprint (dict, optional): Network fingerprint data
            duration (float, optional): Event duration in seconds
            correlation_id (str, optional): ID to group related events
            
        Returns:
            dict: Complete event dictionary with all fields populated
            
        Raises:
            EventValidationError: If any validation fails
            
        Example:
            >>> event = EventFactory.create_event(
            ...     event_type="INTERNET_DOWN",
            ...     device_id="dev-001",
            ...     network_id="net-123",
            ...     description="Internet connection lost",
            ...     metrics={"latency": 500, "loss": 20}
            ... )
        """

        # ====================================================================
        # Step 1: Event Type Validation
        # ====================================================================
        if not is_valid_event_type(event_type):
            raise EventValidationError(
                f"Invalid event_type: {event_type}. "
                f"Must be one of {[e.value for e in EventType]}"
            )

        if event_type not in EventFactory.EVENT_DEFINITIONS:
            raise EventValidationError(
                f"No event definition for type: {event_type}. "
                f"Please add it to EVENT_DEFINITIONS"
            )

        # ====================================================================
        # Step 2: Look Up Event Definition
        # ====================================================================
        definition = EventFactory.EVENT_DEFINITIONS[event_type]

        category = definition["category"]
        severity = definition["severity"]
        summary = definition["summary"]
        verdict = definition["verdict"]
        resolved = definition["resolved"]

        # ====================================================================
        # Step 3: Enum Validation
        # ====================================================================
        if not is_valid_category(category):
            raise EventValidationError(
                f"Invalid category: {category}. "
                f"Must be one of {[c.value for c in Category]}"
            )

        if not is_valid_severity(severity):
            raise EventValidationError(
                f"Invalid severity: {severity}. "
                f"Must be one of {[s.value for s in Severity]}"
            )

        # ====================================================================
        # Step 4: Required Field Validation
        # ====================================================================
        required_fields = {
            "device_id": device_id,
            "network_id": network_id,
            "description": description,
        }

        for name, value in required_fields.items():
            if not value or not isinstance(value, str) or not value.strip():
                raise EventValidationError(
                    f"Missing or invalid field: {name}. "
                    f"Must be a non-empty string."
                )

        # ====================================================================
        # Step 5: Create Event Object
        # ====================================================================
        event = Event(
            type=event_type,
            category=category,
            severity=severity,
            device_id=device_id,
            network_id=network_id,
            verdict=verdict,
            summary=summary,
            description=description,
            metrics=metrics or {},
            fingerprint=fingerprint or {},
            duration=duration,
            resolved=resolved,
            correlation_id=correlation_id,
        )

        # Convert to dictionary for easy serialization
        return asdict(event)


# ============================================================================
# Utility Functions
# ============================================================================

def get_event_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Get all event definitions.
    
    Returns:
        dict: Copy of the event definitions dictionary
        
    Example:
        >>> defs = get_event_definitions()
        >>> for event_type, metadata in defs.items():
        ...     print(f"{event_type}: {metadata['summary']}")
    """
    return EventFactory.EVENT_DEFINITIONS.copy()


def add_event_definition(event_type: str, definition: Dict[str, Any]):
    """
    Add a new event type definition.
    
    This allows runtime extension of event types. Useful for plugins or
    custom deployments.
    
    Args:
        event_type (str): New event type identifier
        definition (dict): Event metadata containing:
            - category: Valid category string
            - severity: Valid severity string
            - summary: Short description
            - verdict: Network verdict
            - resolved: Boolean resolution status
            
    Raises:
        ValueError: If definition is invalid
    """
    # Validate required fields
    required = ['category', 'severity', 'summary', 'verdict', 'resolved']
    for field in required:
        if field not in definition:
            raise ValueError(f"Missing required field in definition: {field}")
    
    # Validate category and severity
    if not is_valid_category(definition['category']):
        raise ValueError(f"Invalid category: {definition['category']}")
    if not is_valid_severity(definition['severity']):
        raise ValueError(f"Invalid severity: {definition['severity']}")
    
    EventFactory.EVENT_DEFINITIONS[event_type] = definition


# Export public interface
__all__ = [
    'Event',
    'EventFactory',
    'EventValidationError',
    'get_event_definitions',
    'add_event_definition'
]
