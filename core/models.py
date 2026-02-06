from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class NetworkState(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Event:
    id: str
    network_id: str
    device_id: str
    severity: str
    message: str
    timestamp: str
    correlation_id: Optional[str] = None
