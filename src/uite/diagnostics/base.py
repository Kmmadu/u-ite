import subprocess
import platform
import socket
import requests
import sys
import argparse
import re


# Removed: from storage.db import init_db, save_run, generate_network_id
# These operations are now handled by the observer (observe.py) or core.fingerprint

# Removed: init_db() - Database initialization is now handled by observe.py

def get_default_gateway():
    """Detect default gateway (router IP)."""
    system = platform.system().lower()

    try:
        if system in ("linux", "darwin"):
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            match = re.search(r"default via ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)

        elif system == "windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            match = re.search(r"Default Gateway[ .]*: ([\d\.]+)", result.stdout)
            if match:
                return match.group(1)
    except Exception:
        pass

    return None


def can_ping(target):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    result = subprocess.run(
        ["ping", param, "1", target],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def can_resolve_dns(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False


def can_open_website(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False


def measure_latency_and_loss(target, count=5):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    result = subprocess.run(
        ["ping", param, str(count), target],
        capture_output=True,
        text=True
    )

    output = result.stdout.lower()

    loss = None
    m = re.search(r'(\d+)%\s*packet loss', output)
    if m:
        loss = int(m.group(1))
    else:
        m = re.search(r'lost = \d+ \((\d+)%\)', output)
        if m:
            loss = int(m.group(1))

    latency = None
    m = re.search(r'[\d\.]+/([\d\.]+)/', output)
    if m:
        latency = float(m.group(1))
    else:
        m = re.search(r'average = (\d+)ms', output)
        if m:
            latency = float(m.group(1))

    return latency, loss


def run_diagnostics(router_ip, internet_ip="8.8.8.8", website="www.google.com", url="https://www.google.com", return_result=False):
    # These parameters are now expected to be provided by the caller (e.g., observe.py)
    # The router_ip is now a mandatory argument for this function.
    ROUTER_IP = router_ip
    INTERNET_IP = internet_ip
    WEBSITE_NAME = website
    WEBSITE_URL = url

    if not ROUTER_IP:
        if not return_result: print("[ERROR] No router IP provided.")
        return None

    if not return_result: print(f"[INFO] Using router IP: {ROUTER_IP}")
    if not return_result: print("--- U-ITE Diagnostic Check Initiated ---")

    router_ok = False
    internet_ok = False
    dns_ok = False
    http_ok = False
    latency = None
    loss = None
    verdict = "Unknown"

    # Check 1: Router
    if can_ping(ROUTER_IP):
        router_ok = True
        if not return_result: print("[PASS] Router reachable")
    else:
        verdict = "Local Network Failure"
        if not return_result: print("[FAIL] Router unreachable")

    # Check 2: Internet
    if router_ok and can_ping(INTERNET_IP):
        internet_ok = True
        if not return_result: print("[PASS] Internet reachable")
    elif router_ok:
        verdict = "ISP Failure"
        if not return_result: print("[FAIL] Internet unreachable")

    # Check 3: DNS
    if internet_ok and can_resolve_dns(WEBSITE_NAME):
        dns_ok = True
        if not return_result: print("[PASS] DNS OK")
    elif internet_ok:
        verdict = "DNS Failure"
        if not return_result: print("[FAIL] DNS failure")

    # Check 4: HTTP
    if dns_ok and can_open_website(WEBSITE_URL):
        http_ok = True
        if not return_result: print("[PASS] HTTP OK")
    elif dns_ok:
        verdict = "Application Failure"
        if not return_result: print("[FAIL] HTTP failure")

    # Check 5: Quality
    if http_ok:
        latency, loss = measure_latency_and_loss(INTERNET_IP)
        if latency is not None and loss is not None:
            if not return_result: print(f"[INFO] Avg latency: {latency:.2f} ms | Packet loss: {loss}%")
            verdict = "Degraded Internet" if loss >= 20 or latency >= 200 else "Healthy"
        else:
            verdict = "Healthy"

    diagnostic_data = {
        "router_ip": ROUTER_IP,
        "internet_ip": INTERNET_IP,
        "router_reachable": router_ok,
        "internet_reachable": internet_ok,
        "dns_ok": dns_ok,
        "http_ok": http_ok,
        "avg_latency": latency,
        "packet_loss": loss,
        "verdict": verdict
    }

    if not return_result:
        # When run as standalone, it still prints the result
        print(f"[RESULT] Verdict: {verdict}")
        print("--- U-ITE Diagnostic Check Complete ---")

    return diagnostic_data

# ---------------- CLI ---------------- #

parser = argparse.ArgumentParser(description="U-ITE Internet Truth Engine")
parser.add_argument("--router", required=False, help="Router IP address. If not provided, attempts to auto-detect.")
parser.add_argument("--internet-ip", default="8.8.8.8", help="Public IP for internet reachability and quality checks.")
parser.add_argument("--website", default="www.google.com", help="Website name for DNS resolution check.")
parser.add_argument("--url", default="https://www.google.com", help="Full URL for HTTP/HTTPS connectivity check.")
args = parser.parse_args()

if __name__ == "__main__":
    # For standalone execution, we need to get the router IP if not provided via CLI
    # Note: get_default_gateway is defined in this file
    detected_router_ip = args.router or get_default_gateway()
    if not detected_router_ip:
        print("[ERROR] Could not determine router IP. Please provide it via --router argument.")
        sys.exit(1)

    run_diagnostics(
        router_ip=detected_router_ip,
        internet_ip=args.internet_ip,
        website=args.website,
        url=args.url,
        return_result=False
    )