from .event_factory import EventFactory
from .event_types import EventType
from .event_state import EventState
import time

class EventDetector:
    """Detects significant network events based on diagnostic snapshots."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.state = EventState()
        
        # Debouncing counters
        self.degraded_count = 0
        self.healthy_count = 0
        self.required_sustained_cycles = 2  # Need 2 consecutive cycles
        
        # Cooldown for status change events
        self.last_status_change_time = 0
        self.status_change_cooldown = 120  # 2 minutes
        
        # Track last health score
        self.last_health_score = 100

    def calculate_severity(self, snapshot):
        """Calculate degradation severity level"""
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
        events = []
        network_id = snapshot.get("network_id")
        verdict = snapshot.get("verdict")
        online = verdict in ["Healthy", "Degraded Internet"]
        current_time = time.time()

        # ---- Network Status Change with Intelligence ----
        if self.state.verdict and verdict != self.state.verdict:
            
            # Handle degradation (Healthy -> Degraded)
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
                    self.degraded_count = 0
            
            # Handle recovery (Degraded -> Healthy)
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
                    self.healthy_count = 0

        # ---- Network Lost (Immediate - no debounce) ----
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

        # ---- Network Restored (Immediate) ----
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

        # Update state
        self.state.update(snapshot)
        return events