import subprocess
import platform
import socket
import requests
import sys
import argparse
import re

def get_default_gateway():
    """
    Attempts to detect the default gateway (router IP).
    Works on Linux/macOS/Windows.
    """
    system = platform.system().lower()

    try:
        if system in ("linux", "darwin"):
            result = subprocess.run(
                ["ip", "route"],
                capture_output=True,
                text=True
            )
            match = re.search(r"default via ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)

        elif system == "windows":
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True
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
        print("[ERROR] Could not auto-detect router IP.")
        print("Please supply it manually using --router <IP>")
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


# [COMMIT] feat: Start main diagnostic flow
print("--- U-ITE Diagnostic Check Initiated ---")

# Check 1: Local network (Router)
if not can_ping(ROUTER_IP):
    print("[ERROR] No active network interface detected.")
    print("Truth: Device is not connected to any network.")
    sys.exit(1)

print(f"[PASS] Check 1: Router ({ROUTER_IP}) is reachable.")

# Check 2: Internet reachability (ISP)
if not can_ping(INTERNET_IP):
    print(f"[FAIL] Check 2: Cannot ping public IP ({INTERNET_IP}).")
    print("Truth: Internet problem is likely within the ISP network.")
    sys.exit(2)

print(f"[PASS] Check 2: Public IP ({INTERNET_IP}) is reachable.")

# Check 3: DNS resolution
if not can_resolve_dns(WEBSITE_NAME):
    print(f"[FAIL] Check 3: Cannot resolve website name ({WEBSITE_NAME}).")
    print("Truth: Internet is working, but name resolution (DNS) is failing.")
    sys.exit(3)

print(f"[PASS] Check 3: Website name ({WEBSITE_NAME}) resolved successfully.")

# Check 4: Application layer
if not can_open_website(WEBSITE_URL):
    print(f"[FAIL] Check 4: Cannot open website ({WEBSITE_URL}).")
    print("Truth: Internet is working, but the destination service is unreachable.")
    sys.exit(4)

print(f"[PASS] Check 4: Website ({WEBSITE_URL}) opened successfully.")
print("Truth: Internet connection is healthy at this time.")

# Check 5: Network quality (Latency & Packet Loss)
latency, loss = measure_latency_and_loss(INTERNET_IP)

if latency is None or loss is None:
    print("[WARN] Could not accurately measure network quality.")
else:
    print(f"[INFO] Avg latency: {latency} ms | Packet loss: {loss}%")

    if loss >= 20 or latency >= 200:
        print("Truth: Internet is reachable but degraded or unstable.")
    else:
        print("Truth: Internet quality is healthy.")


print("--- U-ITE Diagnostic Check Complete ---")
