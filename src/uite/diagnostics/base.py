"""
Network Diagnostics Module for U-ITE
=====================================
Performs low-level network connectivity tests and returns structured results.
This module is platform-independent and works on Linux, macOS, and Windows.

The diagnostic process follows a logical hierarchy:
1. Router reachability (LAN connectivity)
2. Internet reachability (WAN connectivity)
3. DNS resolution
4. HTTP/HTTPS connectivity
5. Quality metrics (latency, packet loss)

Each test builds on the previous ones - if router is unreachable,
further tests are skipped as they would be meaningless.
"""

import subprocess
import platform
import socket
import requests
import sys
import argparse
import re


# ============================================================================
# Windows Console Encoding Fix
# ============================================================================
if sys.platform == "win32":
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)


# ============================================================================
# Network Discovery Functions
# ============================================================================

def get_default_gateway():
    """
    Detect the default gateway (router IP) of the current network.
    
    This is the first step in network diagnostics - we need to know
    the router IP to test LAN connectivity.
    
    Cross-platform implementation:
    - Linux/macOS: Uses 'ip route' command
    - Windows: Uses 'ipconfig' command
    
    Returns:
        str: Router IP address (e.g., "192.168.1.1"), or None if not found
        
    Example:
        >>> router_ip = get_default_gateway()
        >>> print(router_ip)
        '192.168.1.1'
    """
    system = platform.system().lower()

    try:
        if system in ("linux", "darwin"):
            # Linux/macOS: Parse 'ip route' output
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            match = re.search(r"default via ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)

        elif system == "windows":
            # Windows: Parse 'ipconfig' output
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            match = re.search(r"Default Gateway[ .]*: ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)
    except Exception:
        # Silently fail - caller handles None
        pass

    return None


# ============================================================================
# Individual Test Functions
# ============================================================================

def can_ping(target):
    """
    Test if a target IP/host is reachable via ICMP ping.
    
    Uses system ping command with platform-appropriate parameters.
    
    Args:
        target (str): IP address or hostname to ping
        
    Returns:
        bool: True if target responds to ping, False otherwise
        
    Example:
        >>> can_ping("8.8.8.8")
        True
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    result = subprocess.run(
        ["ping", param, "1", target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def can_resolve_dns(hostname):
    """
    Test if a hostname can be resolved to an IP address.
    
    Args:
        hostname (str): Domain name to resolve (e.g., "www.google.com")
        
    Returns:
        bool: True if resolution succeeds, False otherwise
        
    Example:
        >>> can_resolve_dns("www.google.com")
        True
    """
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False


def can_open_website(url):
    """
    Test if a website is accessible via HTTP/HTTPS.
    
    Performs a HEAD request to minimize bandwidth usage.
    
    Args:
        url (str): Full URL to test (e.g., "https://www.google.com")
        
    Returns:
        bool: True if website returns successful status code (<400)
        
    Example:
        >>> can_open_website("https://www.google.com")
        True
    """
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False


def measure_latency_and_loss(target, count=5):
    """
    Measure network quality metrics using multiple ping packets.
    
    Performs a series of pings and extracts:
    - Average latency (ms)
    - Packet loss percentage
    
    Args:
        target (str): IP address to ping
        count (int): Number of ping packets to send
        
    Returns:
        tuple: (avg_latency_ms, packet_loss_pct) or (None, None) if failed
        
    Example:
        >>> latency, loss = measure_latency_and_loss("8.8.8.8")
        >>> print(f"Latency: {latency}ms, Loss: {loss}%")
        'Latency: 15.3ms, Loss: 0%'
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    result = subprocess.run(
        ["ping", param, str(count), target],
        capture_output=True,
        text=True
    )

    output = result.stdout.lower()

    # ========================================================================
    # Extract packet loss percentage - Support multiple formats
    # ========================================================================
    loss = None
    
    # Format 1: Linux/macOS style "X% packet loss"
    m = re.search(r'(\d+)%\s*packet loss', output)
    if m:
        loss = int(m.group(1))
    else:
        # Format 2: Windows style "Lost = X (Y% loss)"
        m = re.search(r'lost = \d+ \((\d+)%\)', output)
        if m:
            loss = int(m.group(1))
        else:
            # Format 3: Windows alternative "(X% loss)"
            m = re.search(r'\((\d+)%\s*loss\)', output)
            if m:
                loss = int(m.group(1))
            else:
                # Format 4: Windows simplified "XX% loss"
                m = re.search(r'(\d+)%\s*loss', output)
                if m:
                    loss = int(m.group(1))

    # ========================================================================
    # Extract average latency - Support multiple formats
    # ========================================================================
    latency = None
    
    # Format 1: Linux style "min/avg/max = 10.2/15.5/20.1 ms"
    m = re.search(r'[\d\.]+/([\d\.]+)/', output)
    if m:
        latency = float(m.group(1))
    else:
        # Format 2: Windows style "Average = 15ms"
        m = re.search(r'average = (\d+)ms', output)
        if m:
            latency = float(m.group(1))
        else:
            # Format 3: Windows with decimals "Average = 15.5ms"
            m = re.search(r'average = ([\d\.]+)ms', output)
            if m:
                latency = float(m.group(1))
            else:
                # Format 4: Alternative "avg = 15.5ms"
                m = re.search(r'avg = ([\d\.]+)ms', output)
                if m:
                    latency = float(m.group(1))

    return latency, loss


# ============================================================================
# Main Diagnostic Function
# ============================================================================

def run_diagnostics(router_ip, internet_ip="8.8.8.8", website="www.google.com", 
                    url="https://www.google.com", return_result=False):
    """
    Run a complete network diagnostic suite.
    
    Performs hierarchical testing:
    1. Router connectivity (LAN)
    2. Internet connectivity (WAN)
    3. DNS resolution
    4. Web access
    5. Quality metrics (latency, loss)
    
    Args:
        router_ip (str): Router IP address (required)
        internet_ip (str): IP to test internet connectivity
        website (str): Domain for DNS test
        url (str): Full URL for HTTP test
        return_result (bool): If True, return dict without printing
        
    Returns:
        dict: Diagnostic results containing:
            - router_ip: The router IP used
            - internet_ip: The internet IP used
            - router_reachable: bool
            - internet_reachable: bool
            - dns_ok: bool
            - http_ok: bool
            - avg_latency: float or None
            - packet_loss: float or None
            - verdict: Human-readable status with emoji
            
    Example:
        >>> result = run_diagnostics("192.168.1.1", return_result=True)
        >>> print(result["verdict"])
        '✅ Connected'
    """
    # Validate input
    if not router_ip:
        if not return_result: 
            print("[ERROR] No router IP provided.")
        return None

    # Optional verbose output
    if not return_result: 
        print(f"[INFO] Using router IP: {router_ip}")
        print("--- U-ITE Diagnostic Check Initiated ---")

    # Initialize result variables
    router_ok = False
    internet_ok = False
    dns_ok = False
    http_ok = False
    latency = None
    loss = None
    verdict = "Unknown"

    # ========================================================================
    # Level 1: Router Connectivity (LAN)
    # ========================================================================
    if can_ping(router_ip):
        router_ok = True
        if not return_result: 
            print("[PASS] Router reachable")
    else:
        verdict = "🔴 No Network Connection"
        if not return_result: 
            print("[FAIL] Router unreachable - Check cables or WiFi")
        # Skip remaining tests - they're meaningless without router
        http_ok = False
        dns_ok = False
        internet_ok = False
        # Compile and return early
        diagnostic_data = {
            "router_ip": router_ip,
            "internet_ip": internet_ip,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        }
        if not return_result:
            print(f"[RESULT] {verdict}")
            print("--- U-ITE Diagnostic Check Complete ---")
        return diagnostic_data

    # ========================================================================
    # Level 2: Internet Connectivity (WAN) - only if router is reachable
    # ========================================================================
    if can_ping(internet_ip):
        internet_ok = True
        if not return_result: 
            print("[PASS] Internet reachable")
    else:
        verdict = "🌍 ISP Outage"
        if not return_result: 
            print("[FAIL] Internet unreachable - Your ISP may be down")
        # Skip remaining tests
        http_ok = False
        dns_ok = False
        # Compile and return early
        diagnostic_data = {
            "router_ip": router_ip,
            "internet_ip": internet_ip,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        }
        if not return_result:
            print(f"[RESULT] {verdict}")
            print("--- U-ITE Diagnostic Check Complete ---")
        return diagnostic_data

    # ========================================================================
    # Level 3: DNS Resolution - only if internet is reachable
    # ========================================================================
    if can_resolve_dns(website):
        dns_ok = True
        if not return_result: 
            print("[PASS] DNS OK")
    else:
        verdict = "🔍 DNS Resolution Failed"
        if not return_result: 
            print("[FAIL] DNS failure - Can't resolve website names")
        # Skip HTTP test
        http_ok = False
        # Compile and return early
        diagnostic_data = {
            "router_ip": router_ip,
            "internet_ip": internet_ip,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        }
        if not return_result:
            print(f"[RESULT] {verdict}")
            print("--- U-ITE Diagnostic Check Complete ---")
        return diagnostic_data

    # ========================================================================
    # Level 4: HTTP/HTTPS Connectivity - only if DNS works
    # ========================================================================
    if can_open_website(url):
        http_ok = True
        if not return_result: 
            print("[PASS] HTTP OK")
    else:
        verdict = "🌐 Web Access Issue"
        if not return_result: 
            print("[FAIL] HTTP failure - Can't load websites")
        # Compile and return early
        diagnostic_data = {
            "router_ip": router_ip,
            "internet_ip": internet_ip,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        }
        if not return_result:
            print(f"[RESULT] {verdict}")
            print("--- U-ITE Diagnostic Check Complete ---")
        return diagnostic_data

    # ========================================================================
    # Level 5: Quality Metrics - only if HTTP works
    # ========================================================================
    latency, loss = measure_latency_and_loss(internet_ip)
    
    # Always use quality metrics if we have them
    if latency is not None or loss is not None:
        if not return_result:
            latency_str = f"{latency:.2f}" if latency is not None else "N/A"
            loss_str = f"{loss}%" if loss is not None else "N/A"
            print(f"[INFO] Avg latency: {latency_str} ms | Packet loss: {loss_str}")
        
        # Determine quality verdict based on available metrics
        if loss is not None and loss >= 20:
            verdict = "⚠️ Unstable Connection"
        elif latency is not None and latency >= 200:
            verdict = "🐢 Slow Connection"
        elif (loss is not None and loss >= 10) or (latency is not None and latency >= 100):
            verdict = "📶 Degraded Performance"
        else:
            verdict = "✅ Connected"
    else:
        # If we couldn't measure anything, assume connected
        verdict = "✅ Connected"

    # Compile results
    diagnostic_data = {
        "router_ip": router_ip,
        "internet_ip": internet_ip,
        "router_reachable": router_ok,
        "internet_reachable": internet_ok,
        "dns_ok": dns_ok,
        "http_ok": http_ok,
        "avg_latency": latency,
        "packet_loss": loss,
        "verdict": verdict
    }

    # Optional final output
    if not return_result:
        print(f"[RESULT] {verdict}")
        print("--- U-ITE Diagnostic Check Complete ---")

    return diagnostic_data


# ============================================================================
# Command-Line Interface (for standalone testing)
# ============================================================================

if __name__ == "__main__":
    """
    Standalone execution for testing and debugging.
    
    Usage:
        python -m uite.diagnostics.base [--router IP] [options]
    
    Examples:
        python -m uite.diagnostics.base --router 192.168.1.1
        python -m uite.diagnostics.base --internet-ip 1.1.1.1
    """
    parser = argparse.ArgumentParser(
        description="U-ITE Internet Truth Engine - Standalone Diagnostic Tool"
    )
    parser.add_argument("--router", required=False, 
                       help="Router IP address. If not provided, attempts to auto-detect.")
    parser.add_argument("--internet-ip", default="8.8.8.8", 
                       help="Public IP for internet reachability and quality checks.")
    parser.add_argument("--website", default="www.google.com", 
                       help="Website name for DNS resolution check.")
    parser.add_argument("--url", default="https://www.google.com", 
                       help="Full URL for HTTP/HTTPS connectivity check.")
    
    args = parser.parse_args()

    # Auto-detect router IP if not provided
    detected_router_ip = args.router or get_default_gateway()
    if not detected_router_ip:
        print("[ERROR] Could not determine router IP. Please provide it via --router argument.")
        sys.exit(1)

    # Run diagnostics and display results
    run_diagnostics(
        router_ip=detected_router_ip,
        internet_ip=args.internet_ip,
        website=args.website,
        url=args.url,
        return_result=False
    )
