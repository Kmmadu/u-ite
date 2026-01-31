import subprocess
import platform
import socket
import requests
import sys
import argparse
import re

from u_ite.storage import init_db, save_run, generate_network_id

def run_diagnostics(
    router_ip=None,
    internet_ip="8.8.8.8",
    website="www.google.com",
    url="https://www.google.com"
):
    """
    Runs a single U-ITE diagnostic cycle and saves the result.
    Designed for reuse by automation services.
    """

    ROUTER_IP = router_ip or get_default_gateway()
    INTERNET_IP = internet_ip
    WEBSITE_NAME = website
    WEBSITE_URL = url

    if not ROUTER_IP:
        print("[ERROR] No active network interface detected.")
        return


def get_default_gateway():
    """Detect default gateway (router IP)."""
    system = platform.system().lower()

    try:
        if system in ("linux", "darwin"):
            result = subprocess.run(
                ["ip", "route"], capture_output=True, text=True
            )
            match = re.search(r"default via ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)

        elif system == "windows":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True
            )
            match = re.search(r"Default Gateway[ .]*: ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass

    return None



# [COMMIT] feat: Parse command-line arguments
parser = argparse.ArgumentParser(
    description="U-ITE: Internet Truth Engine – diagnose where internet problems truly exist"
)

parser.add_argument(
    "--router",
    required=False,
    help="IP address of the local router (optional, auto-detected by default)"
)


parser.add_argument(
    "--internet-ip",
    default="8.8.8.8",
    help="Public IP used to test internet reachability (default: 8.8.8.8)"
)

parser.add_argument(
    "--website",
    default="www.google.com",
    help="Website hostname to test DNS resolution (default: www.google.com)"
)

parser.add_argument(
    "--url",
    default="https://www.google.com",
    help="Website URL to test application-layer connectivity"
)

args = parser.parse_args()


# [COMMIT] feat: Define core diagnostic targets
ROUTER_IP = args.router

if not ROUTER_IP:
    ROUTER_IP = get_default_gateway()
    if ROUTER_IP:
        print(f"[INFO] Auto-detected router IP: {ROUTER_IP}")
    else:
        print("[ERROR] No active network interface detected.")
        print("Truth: Device is not connected to any network.")
        print("Action: Check Wi-Fi, Ethernet cable, or enable network connection.")
        sys.exit(1)

INTERNET_IP = args.internet_ip
WEBSITE_NAME = args.website
WEBSITE_URL = args.url

# [COMMIT] refactor: Abstract ping logic into reusable function
def can_ping(target):
    """
    Returns True if the target responds to ping, otherwise False.
    Uses platform-specific parameters (-n for Windows, -c for Linux/macOS).
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    
    # [COMMIT] chore: Set ping count to 1 for quick check
    command = ["ping", param, "1", target]

    # [COMMIT] fix: Suppress output for cleaner execution
    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # [COMMIT] feat: Return success based on exit code (0 is success)
    return result.returncode == 0

# [COMMIT] feat: Add DNS resolution check function
def can_resolve_dns(hostname):
    """
    Returns True if the hostname can be resolved to an IP address, otherwise False.
    This tests the local DNS resolver chain.
    """
    try:
        # [COMMIT] feat: Attempt to look up the hostname
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        # [COMMIT] fix: Catch socket errors indicating resolution failure
        return False

# [COMMIT] feat: Add application layer connectivity check function
def can_open_website(url):
    """
    Returns True if a successful HTTP connection can be established, otherwise False.
    This tests the full network stack up to the application layer.
    """
    try:
        # [COMMIT] feat: Use a short timeout to prevent hanging
        # [COMMIT] feat: Use HEAD request for efficiency, only checking headers
        response = requests.head(url, timeout=5)
        # [COMMIT] feat: Check for successful status codes (2xx, 3xx)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        # [COMMIT] fix: Catch all requests exceptions (timeout, connection error, etc.)
        return False

def measure_latency_and_loss(target, count=5):
    """
    Sends multiple pings to a target and returns:
    - average latency (ms)
    - packet loss percentage
    Works on Windows and Linux/macOS.
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, str(count), target]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout.lower()
        
        # --- Packet loss ---
        loss = None
        m = re.search(r'(\d+)%\s*packet loss', output)
        if m:
            loss = int(m.group(1))
        else:
            # Windows style
            m = re.search(r'lost = \d+ \((\d+)%\)', output)
            if m:
                loss = int(m.group(1))

        # --- Average latency ---
        avg_latency = None
        # Linux/macOS style
        m = re.search(r'rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/', output)
        if m:
            avg_latency = float(m.group(1))
        else:
            # Sometimes Linux uses slightly different: "min/avg/max/stddev"
            m = re.search(r'=\s*[\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms', output)
            if m:
                avg_latency = float(m.group(1))
            else:
                # Windows style
                m = re.search(r'average = (\d+)ms', output)
                if m:
                    avg_latency = float(m.group(1))

        return avg_latency, loss

    except Exception as e:
        return None, None

def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

    if not is_valid_ip(ROUTER_IP):
        print(f"[ERROR] Invalid router IP detected: {ROUTER_IP}")
        sys.exit(1)

    router_ok = False
    internet_ok = False
    dns_ok = False
    http_ok = False

    latency = None
    loss = None
    verdict = "Unknown"


    # [COMMIT] feat: Start main diagnostic flow
    print("--- U-ITE Diagnostic Check Initiated ---")

    # Check 1: Local network (Router)
    if can_ping(ROUTER_IP):
        router_ok = True
        print(f"[PASS] Check 1: Router ({ROUTER_IP}) is reachable.")
    else:
        print("[FAIL] Check 1: Router unreachable.")
        verdict = "Local Network Failure"

        print("Truth: Device is connected, but cannot reach the router.")
        print("Action: Verify router IP, check router power, LAN cable, or Wi-Fi link.")

        save_run({
            "network_id": generate_network_id(ROUTER_IP, INTERNET_IP),
            "router_ip": ROUTER_IP,
            "internet_ip": INTERNET_IP,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        })
        print("--- U-ITE Diagnostic Check Complete ---")
        sys.exit(0)
    # stop everything here

    # Check 2: Internet reachability (ISP)
    if can_ping(INTERNET_IP):
        internet_ok = True
        print(f"[PASS] Check 2: Public IP reachable.")
    else:
        print("[FAIL] Check 2: Internet unreachable.")
        verdict = "ISP Failure"
        print("Truth: ISP is unreachable. Check your modem/router or ISP service.")
        save_run({
            "network_id": generate_network_id(ROUTER_IP, INTERNET_IP),
            "router_ip": ROUTER_IP,
            "internet_ip": INTERNET_IP,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        })
        print("--- U-ITE Diagnostic Check Complete ---")
        sys.exit(0)  # stop here too

    # Check 3: DNS resolution
    if can_resolve_dns(WEBSITE_NAME):
        dns_ok = True
        print("[PASS] Check 3: DNS resolution OK.")
    else:
        print("[FAIL] Check 3: DNS failure.")
        verdict = "DNS Failure"
        print("Truth: DNS lookup failed. Check DNS settings or try a different DNS server.")
        save_run({
            "network_id": generate_network_id(ROUTER_IP, INTERNET_IP),
            "router_ip": ROUTER_IP,
            "internet_ip": INTERNET_IP,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        })
        print("--- U-ITE Diagnostic Check Complete ---")
        sys.exit(0)  # stop here

    # Check 4: Application layer
    if can_open_website(WEBSITE_URL):
        http_ok = True
        print("[PASS] Check 4: HTTP OK.")
    else:
        print("[FAIL] Check 4: Application layer failure.")
        verdict = "Application Failure"
        print("Truth: Cannot reach the website. Problem may be server-side or network config.")
        save_run({
            "network_id": generate_network_id(ROUTER_IP, INTERNET_IP),
            "router_ip": ROUTER_IP,
            "internet_ip": INTERNET_IP,
            "router_reachable": router_ok,
            "internet_reachable": internet_ok,
            "dns_ok": dns_ok,
            "http_ok": http_ok,
            "avg_latency": latency,
            "packet_loss": loss,
            "verdict": verdict
        })
        print("--- U-ITE Diagnostic Check Complete ---")
        sys.exit(0)  # stop here

    # Check 5: Network quality (Latency & Packet Loss)
    latency, loss = measure_latency_and_loss(INTERNET_IP)
    if latency is not None and loss is not None:
        print(f"[INFO] Avg latency: {latency:.2f} ms | Packet loss: {loss}%")
        if loss >= 20 or latency >= 200:
            verdict = "Degraded Internet"
        else:
            verdict = "Healthy"
    else:
        print("[WARN] Could not accurately measure network quality.")
        verdict = "Healthy"

    # Save final run
    save_run({
        "network_id": generate_network_id(ROUTER_IP, INTERNET_IP),
        "router_ip": ROUTER_IP,
        "internet_ip": INTERNET_IP,
        "router_reachable": router_ok,
        "internet_reachable": internet_ok,
        "dns_ok": dns_ok,
        "http_ok": http_ok,
        "avg_latency": latency,
        "packet_loss": loss,
        "verdict": verdict
    })

    print("--- U-ITE Diagnostic Check Complete ---")

if __name__ == "__main__":
    run_diagnostics(
        router_ip=args.router,
        internet_ip=args.internet_ip,
        website=args.website,
        url=args.url
    )
