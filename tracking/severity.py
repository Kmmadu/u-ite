from enum import Enum


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def is_valid_severity(value) -> bool:
    try:
        Severity(value)
        return True
    except ValueError:
        return False
