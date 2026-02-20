import time
import signal
import sys
import logging
from datetime import datetime, timedelta

# -------- Core Imports --------
try:
    from uite.diagnostics.base import run_diagnostics
    from uite.storage.db import init_db, save_run
    from uite.core.fingerprint import collect_fingerprint, generate_network_id
    from uite.core.device import get_device_id
    from uite.core.formatters import format_duration
    from uite.tracking.event_detector import EventDetector
    from uite.tracking.event_store import save_events
    from uite.tracking.category import Category
    from uite.core.network_profile import NetworkProfileManager

except ImportError as e:
    print(f"Error: Missing core U-ITE modules ({e})")
    sys.exit(1)

# -------- Configuration --------
DEFAULT_INTERVAL = 30
LOG_FILE = "u-ite-observer.log"

DEFAULT_INTERNET_IP = "8.8.8.8"
DEFAULT_WEBSITE_NAME = "www.google.com"
DEFAULT_WEBSITE_URL = "https://www.google.com"

# -------- Logging --------
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

file_handler = logging.FileHandler(LOG_FILE, mode="a", delay=False)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

# Force immediate flush (no reload needed)
file_handler.flush = file_handler.stream.flush

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logger = logging.getLogger("U-ITE-Observer")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.propagate = False

# -------- State --------
class ObserverState:
    def __init__(self):
        self.running = True
        self.outage_started = None  # Track when internet outage began
        self.announced_networks = set()  # Track which networks we've announced
        self.was_offline = False  # Track previous offline state

state = ObserverState()

# -------- Shutdown --------
def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received. Stopping observer...")
    state.running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# -------- Observer Loop --------
def observe(interval=DEFAULT_INTERVAL):

    print("\n" + "=" * 45)
    print("  U-ITE | Continuous Truth Observer")
    print(f"  Interval: {interval}s")
    print(f"  Log File: {LOG_FILE}")
    print("  Press Ctrl+C to stop")
    print("=" * 45 + "\n")

    # -------- Persistent Identity --------
    device_id = get_device_id()
    logger.info(f"Device ID: {device_id}")

    # -------- Init Storage --------
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # -------- Initialize Network Profile Manager --------
    profile_manager = NetworkProfileManager()

    # -------- Event Engine --------
    event_detector = EventDetector(device_id=device_id)

    while state.running:
        start_time = time.time()

        try:
            # -------- NETWORK IDENTITY --------
            fingerprint = collect_fingerprint()
            router_ip = fingerprint.get("default_gateway")
            
            # Determine if we're offline
            is_offline = router_ip is None
            
            # Generate network ID - use a consistent offline ID when offline
            if is_offline:
                # Use a special ID for offline state that won't create new profiles
                network_id = "offline-state"
            else:
                network_id = generate_network_id(fingerprint)

            # -------- NETWORK PROFILING --------
            profile = profile_manager.get_or_create(network_id, fingerprint, is_offline=is_offline)
            
            # Only announce new networks if they're real networks (not offline state)
            if not is_offline and network_id != "offline-state":
                # Check if this is a newly created profile (within the last 5 minutes)
                time_since_first_seen = (datetime.now() - profile.first_seen).total_seconds()
                if time_since_first_seen < 300:  # Less than 5 minutes old
                    if network_id not in state.announced_networks:
                        state.announced_networks.add(network_id)
                        logger.info(f"🆕 New network detected: {profile.name}")
                        logger.info(f"   Run 'uite network list' to see all networks")
                        logger.info(f"   Run 'uite network rename {network_id[:8]} \"My Network\"' to name it")
            
            # If we were offline and now we're online, try to merge profiles
            if not is_offline and state.was_offline:
                # Try to find an offline profile that might match this network
                for pid, old_profile in profile_manager.profiles.items():
                    if pid != network_id and hasattr(old_profile, 'is_offline_network') and old_profile.is_offline_network:
                        # Check if this offline profile might be the same network
                        if router_ip and router_ip in old_profile.notes:
                            if profile_manager.merge_offline_network(pid, network_id):
                                logger.info(f"🔄 Reconnected to {profile.name} (merged offline session)")
                                break
            
            state.was_offline = is_offline

            # -------- DIAGNOSTICS --------
            if not router_ip:
                # Track internet outage
                if state.outage_started is None:
                    state.outage_started = datetime.now()
                    logger.error("🌐 INTERNET DOWN: Router not detected. Please check your internet connection.")
                else:
                    # Calculate outage duration with human-readable format
                    outage_duration = (datetime.now() - state.outage_started).seconds
                    logger.error(f"🌐 Still offline (outage duration: {format_duration(outage_duration)}). Will retry in {interval}s.")
                
                # Skip diagnostic run but still respect interval
                result = None
            else:
                # Internet is back - clear outage flag if it was set
                if state.outage_started is not None:
                    outage_duration = (datetime.now() - state.outage_started).seconds
                    logger.info(f"✅ Internet connection restored after {format_duration(outage_duration)}")
                    state.outage_started = None

                # Run diagnostics
                result = run_diagnostics(
                    router_ip=router_ip,
                    internet_ip=DEFAULT_INTERNET_IP,
                    website=DEFAULT_WEBSITE_NAME,
                    url=DEFAULT_WEBSITE_URL,
                    return_result=True
                )

                if not result:
                    logger.warning("No diagnostic data returned.")
                else:
                    # -------- ENRICH SNAPSHOT --------
                    timestamp = time.time()

                    result.update({
                        "device_id": device_id,
                        "network_id": network_id,
                        "network_name": profile.name,
                        "network_provider": profile.provider,
                        "network_tags": ",".join(profile.tags) if profile.tags else "",
                        "timestamp": timestamp
                    })

                    save_run(result)

                    # -------- EVENT DETECTION --------
                    events = event_detector.analyze(
                        snapshot=result
                    )

                    if events:
                        save_events(events)

                        for event in events:
                            logger.warning(
                                f"EVENT [{event['type']}] | {event['summary']}"
                            )

                    # -------- METRIC LOGGING --------
                    verdict = result.get("verdict", "Unknown")
                    latency = result.get("avg_latency")
                    loss = result.get("packet_loss")

                    msg = f"[{profile.name}] Verdict: {verdict}"
                    if latency is not None and loss is not None:
                        msg += f" | Latency: {latency:.1f}ms | Loss: {loss}%"

                    logger.info(msg)

        except Exception as e:
            logger.error(f"Observer cycle failed: {e}", exc_info=True)

        # -------- Interval Control - ALWAYS EXECUTE THIS --------
        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)

        # Only log sleep time if it's significant
        if sleep_time > 1 and state.running:
            logger.debug(f"Sleeping for {sleep_time:.1f} seconds until next cycle")

        # Break sleep into chunks to allow for clean shutdown
        for _ in range(int(sleep_time)):
            if not state.running:
                break
            time.sleep(1)

        if state.running:
            time.sleep(sleep_time % 1)

    # Log total runtime when stopping
    if 'start_time' in locals():
        total_runtime = int(time.time() - start_time)
        logger.info(f"U-ITE Observer ran for: {format_duration(total_runtime)}")

    logger.info("U-ITE Observer stopped.")

# -------- Entry --------
if __name__ == "__main__":
    interval = DEFAULT_INTERVAL
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            logger.warning("Invalid interval provided. Using default.")

    observe(interval)