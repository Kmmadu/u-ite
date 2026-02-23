"""
Severity Level Enumeration for U-ITE
======================================
Defines the standard severity levels for network events. Severity indicates
the importance and urgency of an event, helping with filtering, alerting,
and prioritization.

The severity levels follow a logical hierarchy from least to most severe:
- INFO:     Informational, no action needed
- LOW:      Minor issue, monitor
- MEDIUM:   Moderate issue, investigate when convenient
- HIGH:     Significant issue, investigate soon
- WARNING:  Warning of potential problem
- CRITICAL: Severe issue, immediate attention required

Each event in the system must have a severity level, ensuring consistent
prioritization across all event types.
"""

from enum import Enum


class Severity(str, Enum):
    """
    Event severity levels.
    
    These levels indicate the importance and urgency of network events.
    They are used for filtering, alerting, and determining response priority.
    
    Values (ordered from least to most severe):
        INFO:     Informational messages, normal operations
                  Examples: Network restored, configuration change
        
        LOW:      Minor issues, no immediate impact
                  Examples: Slight latency increase, single ping failure
        
        MEDIUM:   Moderate issues, may affect some services
                  Examples: Intermittent packet loss, high latency
        
        HIGH:     Significant issues, affecting multiple services
                  Examples: DNS failures, website unreachable
        
        WARNING:  Warning of potential problems
                  Examples: Approaching thresholds, unusual patterns
        
        CRITICAL: Severe issues, immediate attention required
                  Examples: Complete outage, router unreachable
    
    Usage:
        >>> from uite.tracking.severity import Severity
        >>> event_severity = Severity.CRITICAL
        >>> if event_severity == Severity.CRITICAL:
        ...     send_urgent_alert()
        
        >>> # Get string value
        >>> str(Severity.HIGH)
        'HIGH'
    """
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


def is_valid_severity(value) -> bool:
    """
    Validate if a given value is a valid Severity level.
    
    This function checks whether the input can be converted to a Severity
    enum member. It handles both enum instances and strings, making it useful
    for input validation throughout the system.
    
    Args:
        value: Value to check (can be Severity enum or string)
    
    Returns:
        bool: True if value is a valid Severity, False otherwise
    
    Examples:
        >>> is_valid_severity("CRITICAL")
        True
        >>> is_valid_severity("INVALID")
        False
        >>> is_valid_severity(Severity.WARNING)
        True
        >>> is_valid_severity("warning")  # Case-sensitive
        False
    """
    try:
        Severity(value)
        return True
    except ValueError:
        return False


# ============================================================================
# Additional utility functions
# ============================================================================

def get_all_severities() -> list[str]:
    """
    Get a list of all severity level values.
    
    Returns:
        list[str]: All severity strings in order (least to most severe)
        
    Example:
        >>> levels = get_all_severities()
        >>> print(levels)
        ['INFO', 'LOW', 'MEDIUM', 'HIGH', 'WARNING', 'CRITICAL']
    """
    return [s.value for s in Severity]


def get_severity_descriptions() -> dict[str, str]:
    """
    Get human-readable descriptions for each severity level.
    
    Returns:
        dict: Mapping of severity to description
        
    Example:
        >>> desc = get_severity_descriptions()
        >>> print(desc['CRITICAL'])
        'Severe issue, immediate attention required'
    """
    return {
        "INFO": "Informational messages, normal operations",
        "LOW": "Minor issues, no immediate impact",
        "MEDIUM": "Moderate issues, may affect some services",
        "HIGH": "Significant issues, affecting multiple services",
        "WARNING": "Warning of potential problems",
        "CRITICAL": "Severe issue, immediate attention required",
    }


def get_severity_color(severity: Severity) -> str:
    """
    Get a recommended color for displaying a severity level.
    
    Useful for UI/CLI output to visually indicate severity.
    
    Args:
        severity: Severity level
        
    Returns:
        str: ANSI color code or color name
        
    Example:
        >>> color = get_severity_color(Severity.CRITICAL)
        >>> print(f"{color}Critical alert{color_reset}")
    """
    colors = {
        Severity.INFO: "blue",
        Severity.LOW: "cyan",
        Severity.MEDIUM: "yellow",
        Severity.HIGH: "orange",
        Severity.WARNING: "magenta",
        Severity.CRITICAL: "red",
    }
    return colors.get(severity, "white")


def get_severity_emoji(severity: Severity) -> str:
    """
    Get a recommended emoji for a severity level.
    
    Useful for CLI output to make severity visually distinct.
    
    Args:
        severity: Severity level
        
    Returns:
        str: Emoji representing the severity
        
    Example:
        >>> emoji = get_severity_emoji(Severity.CRITICAL)
        >>> print(f"{emoji} Network is down!")
        '🔴 Network is down!'
    """
    emojis = {
        Severity.INFO: "ℹ️",
        Severity.LOW: "🟢",
        Severity.MEDIUM: "🟡",
        Severity.HIGH: "🟠",
        Severity.WARNING: "⚠️",
        Severity.CRITICAL: "🔴",
    }
    return emojis.get(severity, "❓")


def get_severity_level(severity: Severity) -> int:
    """
    Get numeric level for a severity (higher = more severe).
    
    Useful for comparisons and filtering.
    
    Args:
        severity: Severity level
        
    Returns:
        int: Numeric value (1-6, where 6 is most severe)
        
    Example:
        >>> if get_severity_level(event.severity) >= 5:
        ...     print("High severity event")
    """
    levels = {
        Severity.INFO: 1,
        Severity.LOW: 2,
        Severity.MEDIUM: 3,
        Severity.HIGH: 4,
        Severity.WARNING: 5,
        Severity.CRITICAL: 6,
    }
    return levels.get(severity, 0)


# Export public interface
__all__ = [
    'Severity',
    'is_valid_severity',
    'get_all_severities',
    'get_severity_descriptions',
    'get_severity_color',
    'get_severity_emoji',
    'get_severity_level',
]
