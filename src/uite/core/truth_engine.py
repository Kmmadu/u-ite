"""
Truth Engine Module for U-ITE
==============================
Core decision engine that converts raw diagnostic data into network states
and events. This module implements the business logic for determining
network health based on connectivity checks.

The Truth Engine follows a hierarchical decision tree:
1. Router reachability (LAN)
2. Internet reachability (WAN)
3. DNS resolution
4. HTTP connectivity

Each failure level produces appropriate network states and events with
proper severity levels.
"""

from uite.core.models import NetworkState, Event, Severity
from datetime import datetime
import uuid


class TruthEngine:
    """
    Core decision engine for network health evaluation.
    
    This class processes diagnostic data and determines:
    - Current network state (UP/DOWN/DEGRADED)
    - Appropriate event to record
    - Severity level for alerting
    
    The engine is stateless - it evaluates each diagnostic run independently
    based on the provided data.
    
    Example:
        >>> engine = TruthEngine()
        >>> result = engine.evaluate(diagnostic_data)
        >>> print(result["state"])  # NetworkState.UP
        >>> print(result["event"].message)  # Human-readable description
    """

    def evaluate(self, diagnostic_data: dict):
        """
        Convert diagnostic run into network state and event.
        
        Evaluates connectivity data in a hierarchical manner:
        1. Router unreachable → Network DOWN (CRITICAL)
        2. Internet unreachable → Network DOWN (CRITICAL)
        3. DNS/HTTP failures → Network DEGRADED (WARNING)
        4. All OK → Network UP (INFO)
        
        Args:
            diagnostic_data (dict): Diagnostic run data containing:
                - router_reachable (bool): Can ping router?
                - internet_reachable (bool): Can ping internet IP?
                - dns_ok (bool): Can resolve domain names?
                - http_ok (bool): Can fetch web pages?
                - network_id (str): Network identifier
                
        Returns:
            dict: Contains:
                - state (NetworkState): Current network state
                - event (Event): Event object for logging/alerting
                
        Example:
            >>> data = {
            ...     "router_reachable": True,
            ...     "internet_reachable": False,
            ...     "dns_ok": False,
            ...     "http_ok": False,
            ...     "network_id": "a1b2c3d4"
            ... }
            >>> result = engine.evaluate(data)
            >>> result["state"] == NetworkState.DOWN
            True
        """
        # Extract diagnostic values
        router_ok = diagnostic_data["router_reachable"]
        internet_ok = diagnostic_data["internet_reachable"]
        dns_ok = diagnostic_data["dns_ok"]
        http_ok = diagnostic_data["http_ok"]

        network_id = diagnostic_data["network_id"]

        # ======================================================================
        # Network State Determination
        # Hierarchical decision tree from most severe to least severe
        # ======================================================================

        # Level 1: Complete Network Failure
        if not router_ok:
            state = NetworkState.DOWN
            severity = Severity.CRITICAL
            message = "Router unreachable — possible LAN failure"
            description = "Cannot reach the local router. Check cables, WiFi, or router power."

        # Level 2: Internet Failure (but LAN working)
        elif router_ok and not internet_ok:
            state = NetworkState.DOWN
            severity = Severity.CRITICAL
            message = "Internet unreachable — ISP outage suspected"
            description = "Router is reachable but internet connectivity is down. Your ISP may be experiencing issues."

        # Level 3: Partial Service Failure (DNS/HTTP issues)
        elif internet_ok and (not dns_ok or not http_ok):
            state = NetworkState.DEGRADED
            severity = Severity.WARNING
            message = "Partial service failure (DNS/HTTP)"
            
            if not dns_ok and not http_ok:
                description = "DNS resolution and web access are failing despite internet connectivity."
            elif not dns_ok:
                description = "DNS resolution is failing. Websites may not load even though internet is reachable."
            else:  # not http_ok
                description = "Web access is failing. You may be able to ping but not browse."

        # Level 4: Everything Working
        else:
            state = NetworkState.UP
            severity = Severity.INFO
            message = "Network operating normally"
            description = "All connectivity checks passed. Network is healthy."

        # ======================================================================
        # Event Creation
        # Generate a standardized event for this state change
        # ======================================================================
        event = Event(
            id=str(uuid.uuid4()),                    # Unique event identifier
            network_id=network_id,                    # Affected network
            device_id="truth-engine",                  # Source of the event
            severity=severity.value,                   # INFO/WARNING/CRITICAL
            message=message,                            # Short summary
            timestamp=datetime.utcnow().isoformat(),    # When it happened
            correlation_id=None,                         # Can be used to group related events
            # Note: The Event model may need to be extended to include 'description'
            # For now, we store it in the message, but could add a separate field
        )

        # Return both the state and the event
        return {
            "state": state,
            "event": event
        }


# ============================================================================
# Optional: Add helper functions for common evaluation patterns
# ============================================================================
def is_critical_failure(diagnostic_data: dict) -> bool:
    """
    Quick check if the network is completely down.
    
    Args:
        diagnostic_data: Diagnostic run data
        
    Returns:
        bool: True if network is completely down
    """
    return not diagnostic_data.get("router_reachable", False) or \
           not diagnostic_data.get("internet_reachable", False)


def is_degraded(diagnostic_data: dict) -> bool:
    """
    Quick check if the network is degraded but not completely down.
    
    Args:
        diagnostic_data: Diagnostic run data
        
    Returns:
        bool: True if network is degraded
    """
    return (diagnostic_data.get("internet_reachable", False) and
            (not diagnostic_data.get("dns_ok", False) or
             not diagnostic_data.get("http_ok", False)))


# Export public interface
__all__ = ['TruthEngine', 'is_critical_failure', 'is_degraded']
