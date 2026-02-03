import platform
import subprocess
import re
import hashlib
import uuid
import socket
import requests # Using requests for public IP to match internet_truth.py style and robustness
import json

def get_mac_address():
    """Attempts to get the MAC address of the primary network interface."""
    system = platform.system().lower()
    try:
        if system == "windows":
            # On Windows, getmac provides MAC addresses
            result = subprocess.run(["getmac"], capture_output=True, text=True, check=True)
            # Regex to find a MAC address pattern, typically the first active one
            match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)
            if match: return match.group(0).replace("-", ":").upper()
        elif system in ("linux", "darwin"):
            # On Linux, `ip link` is preferred. On macOS, `ifconfig` is common.
            command = ["ip", "link"]
            if system == "darwin":
                command = ["ifconfig"]

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            # Look for MAC address that is not loopback and is UP
            # This regex tries to find MACs associated with active interfaces
            mac_pattern = r"ether\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})"
            matches = re.findall(mac_pattern, result.stdout)
            if matches:
                # Filter out common virtual/loopback MACs if possible, or just take the first valid one
                for mac in matches:
                    if mac != "00:00:00:00:00:00": # Exclude null MAC
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
        # Create a socket to an external address (doesn't actually send data)
        # This is a common trick to get the local IP used for outbound connections
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Connect to a public DNS server
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
    """Generates a unique ID for the network based on its fingerprint.
    A SHA256 hash of the sorted fingerprint items ensures consistency.
    """
    # Convert all fingerprint values to strings for hashing
    # Use json.dumps to ensure consistent string representation for hashing
    canonical = json.dumps(fingerprint, sort_keys=True, default=str) # default=str handles non-JSON serializable types
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]