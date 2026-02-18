import platform
import subprocess
import re
import hashlib
import uuid
import socket
import requests
import json

def get_mac_address():
    """Attempts to get the MAC address of the primary network interface."""
    system = platform.system().lower()
    try:
        if system == "windows":
            result = subprocess.run(["getmac"], capture_output=True, text=True, check=True)
            match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)
            if match: return match.group(0).replace("-", ":").upper()
        elif system in ("linux", "darwin"):
            command = ["ip", "link"]
            if system == "darwin":
                command = ["ifconfig"]

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            mac_pattern = r"ether\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})"
            matches = re.findall(mac_pattern, result.stdout)
            if matches:
                for mac in matches:
                    if mac != "00:00:00:00:00:00":
                        return mac.upper()
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        pass
    return None

def get_default_gateway():
    """Detect default gateway (router IP)."""
    system = platform.system().lower()
    try:
        if system in ("linux", "darwin"):
            result = subprocess.run(["ip", "route"], capture_output=True, text=True, check=True)
            match = re.search(r"default via ([\d\.]+)", result.stdout)
            if match: return match.group(1)
        elif system == "windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, check=True)
            match = re.search(r"Default Gateway[ .]*: ([\d\.]+)", result.stdout)
            if match: return match.group(1)
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        pass
    return None

def get_public_ip():
    """Fetches the public IP address using an external service."""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        if response.status_code == 200: return response.text.strip()
    except requests.exceptions.RequestException:
        pass
    return None

def get_local_ip():
    """Attempts to get the local IP address of the primary network interface."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def get_hostname():
    """Returns the system's hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return None

def get_system_platform():
    """Returns the system platform string."""
    return platform.platform()

def collect_fingerprint():
    """Collects various network attributes to form a fingerprint."""
    fingerprint = {
        "mac_address": get_mac_address(),
        "default_gateway": get_default_gateway(),
        "public_ip": get_public_ip(),
        "local_ip": get_local_ip(),
        "hostname": get_hostname(),
        "system_platform": get_system_platform()
    }
    return fingerprint

def generate_network_id(fingerprint: dict) -> str:
    """Generates a stable network ID using only persistent components."""
    # Use ONLY stable components that shouldn't change between cycles
    stable_components = [
        fingerprint.get('default_gateway', 'unknown'),  # Router IP (stable)
        fingerprint.get('mac_address', 'unknown'),      # MAC address (hardware-bound)
    ]
    
    # Filter out None values
    stable_components = [str(c) for c in stable_components if c is not None and c != 'unknown']
    
    # If both are unknown, fall back to local IP (less stable but better than nothing)
    if not stable_components or stable_components == ['unknown', 'unknown']:
        local_ip = fingerprint.get('local_ip', 'unknown')
        stable_components = [str(local_ip)]
    
    # Create hash from stable components
    raw = "|".join(stable_components)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]