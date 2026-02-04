import socket
import psutil
import platform
import subprocess
from datetime import datetime


def get_ip_address():
    """Get current IP address."""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception:
        return None


def get_active_interface():
    """Return active network interface."""
    stats = psutil.net_if_stats()

    for interface, data in stats.items():
        if data.isup:
            return interface

    return None


def get_wifi_ssid():
    """Attempt to fetch WiFi SSID (Linux only for now)."""
    try:
        if platform.system() == "Linux":
            result = subprocess.check_output(
                ["iwgetid", "-r"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            return result if result else None

    except Exception:
        pass

    return None


def collect_network_snapshot():
    """Return full snapshot of network state."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": get_ip_address(),
        "interface": get_active_interface(),
        "ssid": get_wifi_ssid(),
    }
