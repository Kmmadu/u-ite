from dataclasses import dataclass


@dataclass
class NetworkSnapshot:
    timestamp: str
    ip_address: str
    interface: str
    ssid: str
