"""
Network Fingerprinting Module for U-ITE
========================================
Collects network characteristics to create a stable, unique identifier for each network.
This allows U-ITE to distinguish between different networks (home, office, coffee shop, etc.)
and track performance separately for each.

The fingerprint combines multiple network attributes to create a hash that:
- Remains stable for the same network across reboots
- Changes when you connect to a different network
- Doesn't rely on unstable attributes like public IP (which can change)

Features:
- Cross-platform network attribute collection (Linux, macOS, Windows)
- Stable network ID generation using persistent components
- Fallback mechanisms for offline scenarios
- Privacy-focused (no personal data stored)
"""

import platform
import subprocess
import re
import hashlib
import uuid
import socket
import requests
import json


def get_mac_address():
    """
    Get the MAC address of the primary network interface.
    
    MAC addresses are hardware-bound and provide a stable identifier for the
    network interface. This is used as part of the network fingerprint.
    
    Cross-platform implementation:
    - Windows: Uses 'getmac' command
    - Linux: Uses 'ip link' command
    - macOS: Uses 'ifconfig' command
    
    Returns:
        str: MAC address in format "XX:XX:XX:XX:XX:XX", or None if not found
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Windows: Use getmac command
            result = subprocess.run(["getmac"], capture_output=True, text=True, check=True)
            match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)
            if match:
                # Normalize to colon-separated uppercase
                return match.group(0).replace("-", ":").upper()
                
        elif system in ("linux", "darwin"):
            # Linux/macOS: Use appropriate command
            command = ["ip", "link"]
            if system == "darwin":
                command = ["ifconfig"]  # macOS uses ifconfig

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            # Pattern to match MAC addresses (ether on Linux, ether on macOS)
            mac_pattern = r"ether\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})"
            matches = re.findall(mac_pattern, result.stdout)
            
            if matches:
                # Return first non-zero MAC address (skip null MAC)
                for mac in matches:
                    if mac != "00:00:00:00:00:00":
                        return mac.upper()
                        
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        # Silently fail if any error occurs - we'll use fallback methods
        pass
        
    return None


def get_default_gateway():
    """
    Detect the default gateway (router IP) of the current network.
    
    The router IP is one of the most stable network identifiers - it only
    changes when you connect to a different router/network.
    
    Cross-platform implementation:
    - Linux/macOS: Uses 'ip route' to find default gateway
    - Windows: Uses 'ipconfig' to find default gateway
    
    Returns:
        str: Router IP address (e.g., "192.168.1.1"), or None if not found
    """
    system = platform.system().lower()
    
    try:
        if system in ("linux", "darwin"):
            # Linux/macOS: Parse 'ip route' output
            result = subprocess.run(["ip", "route"], capture_output=True, text=True, check=True)
            match = re.search(r"default via ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)
                
        elif system == "windows":
            # Windows: Parse 'ipconfig' output
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, check=True)
            match = re.search(r"Default Gateway[ .]*: ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)
                
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        pass
        
    return None


def get_public_ip():
    """
    Fetch the public IP address using an external service.
    
    Note: Public IP is NOT used in the stable network ID because it can change
    even on the same network (DHCP lease renewal, ISP changes). This is only
    collected for informational purposes.
    
    Uses ipify.org - a simple, reliable public IP API.
    
    Returns:
        str: Public IP address, or None if unreachable
    """
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except requests.exceptions.RequestException:
        pass
    return None


def get_local_ip():
    """
    Get the local IP address of the primary network interface.
    
    Uses a clever trick: creates a UDP socket to an external address
    (doesn't actually send data) to determine the local IP used for
    outbound connections.
    
    Returns:
        str: Local IP address (e.g., "192.168.1.100"), or None if not found
    """
    try:
        # Create a UDP socket (doesn't establish connection)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to a public DNS server (doesn't send data)
        s.connect(("8.8.8.8", 80))
        # Get the local IP used for this connection
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def get_hostname():
    """
    Get the system's hostname.
    
    The hostname is collected for informational purposes but is NOT used
    in the stable network ID as it can be changed by the user.
    
    Returns:
        str: System hostname, or None if not available
    """
    try:
        return socket.gethostname()
    except Exception:
        return None


def get_system_platform():
    """
    Get the system platform string.
    
    Provides OS version information for debugging and compatibility checking.
    
    Returns:
        str: Platform string (e.g., "Linux-5.15.0-x86_64")
    """
    return platform.platform()


def collect_fingerprint():
    """
    Collect all network attributes into a fingerprint dictionary.
    
    This gathers both stable and variable network characteristics.
    The stable components are used for network identification, while
    variable components provide additional context.
    
    Returns:
        dict: Dictionary containing all network attributes:
            - mac_address: Hardware MAC address
            - default_gateway: Router IP
            - public_ip: External IP (variable)
            - local_ip: Internal IP (variable)
            - hostname: System hostname (variable)
            - system_platform: OS information
    """
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
    """
    Generate a stable, unique network ID using only persistent components.
    
    The network ID is designed to:
    - Remain constant for the same physical network
    - Change when connecting to a different network
    - Be resilient to temporary changes (DHCP lease renewal, etc.)
    
    Strategy:
    1. Use router IP (stable) and MAC address (hardware-bound) as primary components
    2. If both are unknown (offline), fall back to local IP
    3. Create a hash of these components for a compact, consistent ID
    
    Args:
        fingerprint (dict): Fingerprint dictionary from collect_fingerprint()
        
    Returns:
        str: 16-character hexadecimal network ID
        
    Example:
        >>> fp = collect_fingerprint()
        >>> network_id = generate_network_id(fp)
        >>> print(network_id)
        'a1b2c3d4e5f67890'
    """
    # Use ONLY stable components that shouldn't change between cycles
    stable_components = [
        fingerprint.get('default_gateway', 'unknown'),  # Router IP (stable)
        fingerprint.get('mac_address', 'unknown'),      # MAC address (hardware-bound)
    ]
    
    # Filter out None values and 'unknown' placeholders
    stable_components = [str(c) for c in stable_components if c is not None and c != 'unknown']
    
    # If both are unknown (offline mode), fall back to local IP
    # This is less stable but better than nothing for offline detection
    if not stable_components or stable_components == ['unknown', 'unknown']:
        local_ip = fingerprint.get('local_ip', 'unknown')
        stable_components = [str(local_ip)]
    
    # Create a hash from the stable components
    # Using SHA-256 and truncating to 16 chars gives us a good balance
    # of uniqueness and readability
    raw = "|".join(stable_components)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# Optional: Add a function to generate a human-readable network name
def generate_network_name(fingerprint: dict) -> str:
    """
    Generate a human-readable name suggestion for the network.
    
    This can be used to suggest a friendly name when a new network is detected.
    
    Args:
        fingerprint (dict): Fingerprint dictionary
        
    Returns:
        str: Suggested network name
    """
    gateway = fingerprint.get('default_gateway', '')
    if gateway:
        # Use last octet of gateway IP for a simple name
        parts = gateway.split('.')
        if len(parts) == 4:
            return f"Network {parts[-1]}"
    
    # Fallback to generic name
    return "Unknown Network"
