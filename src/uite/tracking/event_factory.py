import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any

from tracking.event_types import EventType, is_valid_event_type
from tracking.category import Category, is_valid_category
from tracking.severity import Severity, is_valid_severity


# ------------------------------
# Custom Exceptions
# ------------------------------

class EventValidationError(Exception):
    pass


# ------------------------------
# Event Schema
# ------------------------------

@dataclass
class Event:

    event_id: str = field(init=False)
    timestamp: str = field(init=False)

    type: str
    category: str
    severity: str

    device_id: str
    network_id: str
    verdict: str
    summary: str
    description: str

    metrics: Dict[str, Any] = field(default_factory=dict)
    fingerprint: Dict[str, Any] = field(default_factory=dict)

    duration: Optional[float] = None
    resolved: bool = False
    correlation_id: Optional[str] = None

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ------------------------------
# Factory
# ------------------------------

class EventFactory:

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

        # ---------- Event Type Validation ----------

        if not is_valid_event_type(event_type):
            raise EventValidationError(f"Invalid event_type: {event_type}")

        if event_type not in EventFactory.EVENT_DEFINITIONS:
            raise EventValidationError(f"No event definition for type: {event_type}")

        definition = EventFactory.EVENT_DEFINITIONS[event_type]

        category = definition["category"]
        severity = definition["severity"]
        summary = definition["summary"]
        verdict = definition["verdict"]
        resolved = definition["resolved"]

        # ---------- Enum Validation ----------

        if not is_valid_category(category):
            raise EventValidationError(f"Invalid category: {category}")

        if not is_valid_severity(severity):
            raise EventValidationError(f"Invalid severity: {severity}")

        # ---------- Required Field Validation ----------

        required_fields = {
            "device_id": device_id,
            "network_id": network_id,
            "description": description,
        }

        for name, value in required_fields.items():
            if not value or not isinstance(value, str) or not value.strip():
                raise EventValidationError(f"Missing or invalid field: {name}")

        # ---------- Create Event ----------

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

        return asdict(event)
