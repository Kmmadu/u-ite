import time
import signal
import sys
import logging

# -------- Core Imports --------
try:
    from internet_truth import run_diagnostics
    from storage.db import init_db, save_run
    from core.fingerprint import collect_fingerprint, generate_network_id
    from core.device import get_device_id
    from tracking.event_detector import EventDetector
    from tracking.event_store import save_events
    from tracking.category import Category


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

    # -------- Event Engine --------
    event_detector = EventDetector(device_id=device_id)

    while state.running:
        start_time = time.time()

        try:
            # -------- NETWORK IDENTITY --------
            fingerprint = collect_fingerprint()
            network_id = generate_network_id(fingerprint)

            # -------- DIAGNOSTICS --------
            router_ip = fingerprint.get("default_gateway")
            if not router_ip:
                logger.error("Router IP not detected. Skipping cycle.")
                continue

            result = run_diagnostics(
                router_ip=router_ip,
                internet_ip=DEFAULT_INTERNET_IP,
                website=DEFAULT_WEBSITE_NAME,
                url=DEFAULT_WEBSITE_URL,
                return_result=True
            )

            if not result:
                logger.warning("No diagnostic data returned.")
                continue

            # -------- ENRICH SNAPSHOT --------
            timestamp = time.time()

            result.update({
                "device_id": device_id,
                "network_id": network_id,
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

            msg = f"Verdict: {verdict}"
            if latency is not None and loss is not None:
                msg += f" | Latency: {latency:.1f}ms | Loss: {loss}%"

            logger.info(msg)

        except Exception as e:
            logger.error(f"Observer cycle failed: {e}", exc_info=True)

        # -------- Interval Control --------
        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)

        for _ in range(int(sleep_time)):
            if not state.running:
                break
            time.sleep(1)

        if state.running:
            time.sleep(sleep_time % 1)

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