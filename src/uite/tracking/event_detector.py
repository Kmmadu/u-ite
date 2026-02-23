"""
Event Detection Module for U-ITE
==================================
Detects significant network events by analyzing diagnostic snapshots and
comparing them with historical state. Uses intelligent debouncing to prevent
alert fatigue from transient issues.

Features:
- Stateful tracking of network conditions
- Intelligent debouncing for status changes
- Severity calculation based on metrics
- Cooldown periods to prevent event storms
- Immediate detection of critical events (down/restored)
- Sustained condition verification before alerting
"""

from .event_factory import EventFactory
from .event_types import EventType
from .event_state import EventState
import time


class EventDetector:
    """
    Detects significant network events based on diagnostic snapshots.
    
    This class maintains state between snapshots and uses intelligent
    algorithms to detect meaningful network events while filtering out
    transient fluctuations.
    
    The detector uses:
    - Sustained condition detection (multiple consecutive cycles)
    - Cooldown periods to prevent event storms
    - Severity levels based on metrics
    - Immediate alerts for critical events
    
    Example:
        >>> detector = EventDetector(device_id="dev-001")
        >>> events = detector.analyze(snapshot)
        >>> for event in events:
        ...     print(f"Detected: {event['type']}")
    """

    def __init__(self, device_id: str):
        """
        Initialize the event detector.
        
        Args:
            device_id (str): Unique identifier for this device
        """
        self.device_id = device_id
        self.state = EventState()
        
        # ====================================================================
        # Debouncing Configuration
        # Prevents alert fatigue from transient issues
        # ====================================================================
        self.degraded_count = 0
        self.healthy_count = 0
        self.required_sustained_cycles = 2  # Need 2 consecutive cycles
        
        # Cooldown for status change events (prevents spam)
        self.last_status_change_time = 0
        self.status_change_cooldown = 120  # 2 minutes in seconds
        
        # Track last health score for trend analysis
        self.last_health_score = 100

    def calculate_severity(self, snapshot):
        """
        Calculate degradation severity level based on metrics.
        
        Evaluates latency and packet loss to determine severity:
        - CRITICAL: Loss >20% or Latency >500ms
        - SEVERE:   Loss >10% or Latency >200ms
        - MODERATE: Loss >5%  or Latency >100ms
        - MILD:     Minor degradation
        
        Args:
            snapshot (dict): Diagnostic snapshot containing metrics
            
        Returns:
            tuple: (severity_level, description_string)
            
        Example:
            >>> severity, desc = detector.calculate_severity(snapshot)
            >>> print(f"{severity}: {desc}")
            'CRITICAL: Critical - Latency: 523ms, Loss: 25%'
        """
        latency = snapshot.get("metrics", {}).get("avg_latency", 0)
        loss = snapshot.get("metrics", {}).get("packet_loss", 0)
        
        if loss > 20 or latency > 500:
            return "CRITICAL", f"Critical - Latency: {latency}ms, Loss: {loss}%"
        elif loss > 10 or latency > 200:
            return "SEVERE", f"Severe - Latency: {latency}ms, Loss: {loss}%"
        elif loss > 5 or latency > 100:
            return "MODERATE", f"Moderate - Latency: {latency}ms, Loss: {loss}%"
        else:
            return "MILD", f"Mild - Latency: {latency}ms, Loss: {loss}%"

    def analyze(self, snapshot: dict) -> list[dict]:
        """
        Analyze a diagnostic snapshot and detect events.
        
        This is the main entry point for event detection. It compares the
        current snapshot with the previous state and generates appropriate
        events based on changes.
        
        Detection logic:
        1. Status changes (degradation/recovery) - debounced
        2. Network lost - immediate
        3. Network restored - immediate
        
        Args:
            snapshot (dict): Diagnostic snapshot containing:
                - network_id: Network identifier
                - verdict: Current network verdict
                - metrics: Performance metrics
                
        Returns:
            list[dict]: List of detected events, each ready for storage
                       via EventFactory
                       
        Example:
            >>> events = detector.analyze(snapshot)
            >>> if events:
            ...     for event in events:
            ...         print(f"Event: {event['type']}")
        """
        events = []
        network_id = snapshot.get("network_id")
        verdict = snapshot.get("verdict")
        online = verdict in ["Healthy", "Degraded Internet"]
        current_time = time.time()

        # ====================================================================
        # Network Status Change with Intelligent Debouncing
        # Only alert after sustained condition and cooldown period
        # ====================================================================
        if self.state.verdict and verdict != self.state.verdict:
            
            # Case 1: Network Degradation (Healthy -> Degraded)
            if verdict in ["Degraded Internet", "ISP Failure", "Application Failure"]:
                self.degraded_count += 1
                self.healthy_count = 0
                
                # Only alert after sustained degradation
                if (self.degraded_count >= self.required_sustained_cycles and
                    current_time - self.last_status_change_time > self.status_change_cooldown):
                    
                    severity, description = self.calculate_severity(snapshot)
                    self.last_status_change_time = current_time
                    
                    events.append(
                        EventFactory.create_event(
                            event_type=EventType.NETWORK_STATUS_CHANGE.value,
                            device_id=self.device_id,
                            network_id=network_id,
                            description=f"Network degraded ({severity}): {description}",
                            metrics=snapshot.get("metrics", {})
                        )
                    )
                    self.degraded_count = 0  # Reset after alert
            
            # Case 2: Network Recovery (Degraded -> Healthy)
            elif verdict == "Healthy":
                self.healthy_count += 1
                self.degraded_count = 0
                
                if (self.healthy_count >= self.required_sustained_cycles and
                    current_time - self.last_status_change_time > self.status_change_cooldown):
                    
                    self.last_status_change_time = current_time
                    events.append(
                        EventFactory.create_event(
                            event_type=EventType.NETWORK_STATUS_CHANGE.value,
                            device_id=self.device_id,
                            network_id=network_id,
                            description=f"Network recovered to Healthy after {self.state.verdict}",
                            metrics=snapshot.get("metrics", {})
                        )
                    )
                    self.healthy_count = 0  # Reset after alert

        # ====================================================================
        # Critical Events - No Debouncing
        # These events are important enough to alert immediately
        # ====================================================================
        
        # Network Lost (Immediate)
        if self.state.online is True and online is False:
            events.append(
                EventFactory.create_event(
                    event_type=EventType.INTERNET_DOWN.value,
                    device_id=self.device_id,
                    network_id=network_id,
                    description=f"Internet connectivity lost. Last verdict: {self.state.verdict}",
                    metrics=snapshot.get("metrics", {})
                )
            )

        # Network Restored (Immediate)
        if self.state.online is False and online is True:
            events.append(
                EventFactory.create_event(
                    event_type=EventType.NETWORK_RESTORED.value,
                    device_id=self.device_id,
                    network_id=network_id,
                    description=f"Internet connectivity restored after being offline",
                    metrics=snapshot.get("metrics", {})
                )
            )

        # Update internal state for next cycle
        self.state.update(snapshot)
        return events


# ============================================================================
# Utility Functions
# ============================================================================

def create_detector_with_defaults(device_id: str) -> EventDetector:
    """
    Create an EventDetector with standard configuration.
    
    This factory function creates a detector with sensible defaults:
    - 2 cycles sustained detection
    - 2 minute cooldown
    - Standard severity thresholds
    
    Args:
        device_id (str): Device identifier
        
    Returns:
        EventDetector: Configured detector instance
    """
    detector = EventDetector(device_id)
    # Defaults are already set in __init__
    return detector


def configure_detector_for_sensitivity(detector: EventDetector, sensitivity: str):
    """
    Adjust detector sensitivity.
    
    Args:
        detector: EventDetector instance
        sensitivity: 'low', 'medium', or 'high'
        
    Returns:
        None
    """
    if sensitivity == 'high':
        detector.required_sustained_cycles = 1
        detector.status_change_cooldown = 30
    elif sensitivity == 'low':
        detector.required_sustained_cycles = 3
        detector.status_change_cooldown = 300
    else:  # medium (default)
        detector.required_sustained_cycles = 2
        detector.status_change_cooldown = 120


# Export public interface
__all__ = ['EventDetector', 'create_detector_with_defaults', 'configure_detector_for_sensitivity']
