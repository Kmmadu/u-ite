import sys
# Save original argv and temporarily set it to just the script name
# This prevents imported modules from parsing our CLI arguments
original_argv = sys.argv
sys.argv = [sys.argv[0]]

import time
import signal
import logging
from datetime import datetime
from pathlib import Path

# Now do the imports - they won't see our --interval flag
try:
    from uite.diagnostics.base import run_diagnostics
    from uite.storage.db import init_db, save_run
    from uite.core.fingerprint import collect_fingerprint, generate_network_id
    from uite.core.device import get_device_id
    from uite.core.formatters import format_duration
    from uite.tracking.event_detector import EventDetector
    from uite.tracking.event_store import save_events
    from uite.core.network_profile import NetworkProfileManager
    from uite.core.platform import OS
except ImportError as e:
    print(f"Error: Missing core U-ITE modules ({e})")
    sys.exit(1)

# Restore original argv after imports are done
sys.argv = original_argv

DEFAULT_INTERVAL = 30
DEFAULT_INTERNET_IP = "8.8.8.8"
DEFAULT_WEBSITE_NAME = "www.google.com"
DEFAULT_WEBSITE_URL = "https://www.google.com"

LOG_DIR = OS.get_log_dir()
LOG_FILE = LOG_DIR / "uite-observer.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler = logging.FileHandler(LOG_FILE, mode="a", delay=False)
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logger = logging.getLogger("U-ITE-Observer")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

class ObserverState:
    def __init__(self):
        self.running = True
        self.outage_started = None
        self.announced_networks = set()
        self.was_offline = False

state = ObserverState()

def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received. Stopping observer...")
    state.running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

def observe(interval=DEFAULT_INTERVAL, router_ip_override=None, internet_ip=DEFAULT_INTERNET_IP, website=DEFAULT_WEBSITE_NAME, url=DEFAULT_WEBSITE_URL):
    print(f"\n🔍 U-ITE Network Observer (interval: {interval}s)")
    print("-" * 40)

    device_id = get_device_id()
    init_db()
    profile_manager = NetworkProfileManager()
    event_detector = EventDetector(device_id=device_id)

    while state.running:
        start_time = time.time()
        try:
            fingerprint = collect_fingerprint()
            router_ip = router_ip_override or fingerprint.get("default_gateway")
            is_offline = router_ip is None
            network_id = "offline-state" if is_offline else generate_network_id(fingerprint)
            profile = profile_manager.get_or_create(network_id, fingerprint, is_offline=is_offline)
            
            if not is_offline:
                if state.outage_started:
                    state.outage_started = None
                
                result = run_diagnostics(router_ip=router_ip, internet_ip=internet_ip, website=website, url=url, return_result=True)
                if result:
                    result.update({"device_id": device_id, "network_id": network_id, "timestamp": time.time()})
                    save_run(result)
                    events = event_detector.analyze(snapshot=result)
                    if events: 
                        save_events(events)
                    logger.info(f"[{profile.name}] Verdict: {result.get('verdict')} | Latency: {result.get('avg_latency')}ms | Loss: {result.get('packet_loss')}%")
            else:
                if state.outage_started is None: 
                    state.outage_started = datetime.now()
                logger.error("🌐 INTERNET DOWN")

        except Exception as e:
            logger.error(f"Observer cycle failed: {e}", exc_info=True)

        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        for _ in range(int(sleep_time)):
            if not state.running: break
            time.sleep(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='U-ITE Network Observer')
    parser.add_argument('--interval', type=int, default=DEFAULT_INTERVAL, help='Check interval in seconds')
    parser.add_argument('--router', help='Router IP override')
    parser.add_argument('--internet-ip', default=DEFAULT_INTERNET_IP, help='Internet IP to check')
    parser.add_argument('--website', default=DEFAULT_WEBSITE_NAME, help='Website to check')
    parser.add_argument('--url', default=DEFAULT_WEBSITE_URL, help='URL to check')
    
    args = parser.parse_args()
    print(f"Starting U-ITE observer with interval: {args.interval}s")
    observe(interval=args.interval, router_ip_override=args.router, 
            internet_ip=args.internet_ip, website=args.website, url=args.url)