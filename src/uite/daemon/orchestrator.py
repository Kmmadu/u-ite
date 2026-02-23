"""
U-ITE Orchestrator Daemon
==========================
Main continuous monitoring loop that runs network diagnostics periodically.
This is the core engine that drives all data collection and event detection.

The orchestrator:
1. Runs indefinitely at specified intervals
2. Collects network fingerprints
3. Runs diagnostics (ping, DNS, HTTP)
4. Updates network profiles
5. Detects and stores events
6. Handles offline states gracefully
7. Responds to shutdown signals

This module can be run directly or imported and called programmatically.
"""

import sys
# ======================================================================
# Argument Protection
# Temporarily hide CLI arguments from imported modules
# This prevents modules like argparse in dependencies from consuming
# our command-line arguments before we get to parse them.
# ======================================================================
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
    from uite.storage.event_store import EventStore  # FIXED: Import from storage
    from uite.core.network_profile import NetworkProfileManager
    from uite.core.platform import OS
except ImportError as e:
    print(f"Error: Missing core U-ITE modules ({e})")
    sys.exit(1)

# Restore original argv after imports are done
sys.argv = original_argv

# ======================================================================
# Configuration Constants
# ======================================================================
DEFAULT_INTERVAL = 30  # Default check interval in seconds
DEFAULT_INTERNET_IP = "8.8.8.8"  # Google DNS for internet checks
DEFAULT_WEBSITE_NAME = "www.google.com"  # Website for DNS checks
DEFAULT_WEBSITE_URL = "https://www.google.com"  # URL for HTTP checks

# ======================================================================
# Logging Configuration
# Uses OS-appropriate paths for cross-platform compatibility
# ======================================================================
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


# ======================================================================
# Observer State
# Maintains runtime state across monitoring cycles
# ======================================================================
class ObserverState:
    """
    Runtime state for the observer daemon.
    
    Attributes:
        running (bool): Whether the observer should continue running
        outage_started (datetime): When current outage began (None if no outage)
        announced_networks (set): Networks already announced as "new"
        was_offline (bool): Whether we were offline in previous cycle
    """
    def __init__(self):
        self.running = True
        self.outage_started = None
        self.announced_networks = set()
        self.was_offline = False


state = ObserverState()


# ======================================================================
# Signal Handlers
# Handle graceful shutdown on SIGINT (Ctrl+C) and SIGTERM
# ======================================================================
def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received. Stopping observer...")
    state.running = False


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# ======================================================================
# Main Observer Loop
# ======================================================================
def observe(interval=DEFAULT_INTERVAL, router_ip_override=None, 
            internet_ip=DEFAULT_INTERNET_IP, website=DEFAULT_WEBSITE_NAME, 
            url=DEFAULT_WEBSITE_URL):
    """
    Run the continuous network monitoring loop.
    
    This is the main entry point for the daemon. It performs the following
    operations in each cycle:
    1. Collect network fingerprint
    2. Generate/update network profile
    3. Run diagnostics (if online)
    4. Save results to database
    5. Detect and save events
    6. Log results
    
    Args:
        interval (int): Seconds between diagnostic checks
        router_ip_override (str, optional): Force a specific router IP
        internet_ip (str): IP to check for internet connectivity
        website (str): Website name for DNS checks
        url (str): Full URL for HTTP checks
        
    Example:
        >>> observe(interval=60)  # Run every 60 seconds
    """
    print(f"\n🔍 U-ITE Network Observer (interval: {interval}s)")
    print("-" * 40)

    # Initialize components
    device_id = get_device_id()
    init_db()
    profile_manager = NetworkProfileManager()
    event_detector = EventDetector(device_id=device_id)

    # Main monitoring loop
    while state.running:
        start_time = time.time()
        
        try:
            # ==============================================================
            # Network Identification
            # ==============================================================
            fingerprint = collect_fingerprint()
            router_ip = router_ip_override or fingerprint.get("default_gateway")
            is_offline = router_ip is None
            
            # Generate network ID (special ID for offline state)
            network_id = "offline-state" if is_offline else generate_network_id(fingerprint)
            
            # Get or create network profile
            profile = profile_manager.get_or_create(network_id, fingerprint, is_offline=is_offline)
            
            # ==============================================================
            # Diagnostics (only when online)
            # ==============================================================
            if not is_offline:
                # Clear outage flag if it was set
                if state.outage_started:
                    state.outage_started = None
                
                # Run comprehensive diagnostics
                result = run_diagnostics(
                    router_ip=router_ip, 
                    internet_ip=internet_ip, 
                    website=website, 
                    url=url, 
                    return_result=True
                )
                
                if result:
                    # Enrich result with metadata
                    result.update({
                        "device_id": device_id, 
                        "network_id": network_id, 
                        "timestamp": time.time()
                    })
                    
                    # Save to database
                    save_run(result)
                    
                    # Detect and save events - FIXED: Use EventStore
                    events = event_detector.analyze(snapshot=result)
                    if events: 
                        for event in events:
                            EventStore.save_event(event)
                    
                    # Log the verdict
                    logger.info(
                        f"[{profile.name}] Verdict: {result.get('verdict')} | "
                        f"Latency: {result.get('avg_latency')}ms | "
                        f"Loss: {result.get('packet_loss')}%"
                    )
            
            # ==============================================================
            # Offline Handling
            # ==============================================================
            else:
                if state.outage_started is None: 
                    state.outage_started = datetime.now()
                logger.error("🌐 INTERNET DOWN")

        except Exception as e:
            logger.error(f"Observer cycle failed: {e}", exc_info=True)

        # ==============================================================
        # Interval Control
        # Sleep for the remaining time to maintain the interval
        # ==============================================================
        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        
        # Sleep in 1-second chunks to allow for responsive shutdown
        for _ in range(int(sleep_time)):
            if not state.running: 
                break
            time.sleep(1)


# ======================================================================
# Entry Point
# ======================================================================
if __name__ == "__main__":
    """
    Command-line entry point for direct execution.
    
    Usage:
        python -m uite.daemon.orchestrator [--interval N] [--router IP] ...
    
    Examples:
        python -m uite.daemon.orchestrator --interval 60
        python -m uite.daemon.orchestrator --router 192.168.1.1
    """
    import argparse
    parser = argparse.ArgumentParser(description='U-ITE Network Observer')
    parser.add_argument('--interval', type=int, default=DEFAULT_INTERVAL, 
                       help='Check interval in seconds')
    parser.add_argument('--router', help='Router IP override')
    parser.add_argument('--internet-ip', default=DEFAULT_INTERNET_IP, 
                       help='Internet IP to check')
    parser.add_argument('--website', default=DEFAULT_WEBSITE_NAME, 
                       help='Website to check')
    parser.add_argument('--url', default=DEFAULT_WEBSITE_URL, 
                       help='URL to check')
    
    args = parser.parse_args()
    print(f"Starting U-ITE observer with interval: {args.interval}s")
    observe(
        interval=args.interval, 
        router_ip_override=args.router, 
        internet_ip=args.internet_ip, 
        website=args.website, 
        url=args.url
    )