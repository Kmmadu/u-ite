import time
import signal
import sys
import logging

# -------- Core Imports --------
try:
    from internet_truth import run_diagnostics
    from storage.db import init_db, save_run
    from core.fingerprint import collect_fingerprint, generate_network_id
except ImportError as e:
    print(f"Error: Missing core U-ITE modules ({e})")
    sys.exit(1)

# -------- Configuration --------
DEFAULT_INTERVAL = 60
LOG_FILE = "u-ite-observer.log"

# Default diagnostic targets (can be made configurable later)
DEFAULT_INTERNET_IP = "8.8.8.8"
DEFAULT_WEBSITE_NAME = "www.google.com"
DEFAULT_WEBSITE_URL = "https://www.google.com"

# -------- Logging (Single Source of Truth) --------
log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

file_handler = logging.FileHandler(LOG_FILE, mode="a", delay=False)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

# Force immediate flush to disk (no reload needed)
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
        self.last_network_id = None
        self.last_fingerprint = None

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

    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    while state.running:
        start_time = time.time()

        try:
            # -------- NETWORK IDENTITY LAYER --------
            fingerprint = collect_fingerprint()
            network_id = generate_network_id(fingerprint)

            if state.last_network_id and network_id != state.last_network_id:
                logger.warning("NETWORK CHANGE DETECTED")
                logger.info(f"Old Network ID: {state.last_network_id}")
                logger.info(f"New Network ID: {network_id}")
                logger.debug(f"Old Fingerprint: {state.last_fingerprint}")
                logger.debug(f"New Fingerprint: {fingerprint}")

            state.last_network_id = network_id
            state.last_fingerprint = fingerprint

            # -------- DIAGNOSTIC LAYER --------
            # Get the router IP from the fingerprint to pass to the diagnostic engine
            router_ip = fingerprint.get("default_gateway")
            if not router_ip:
                logger.error("Could not determine router IP from fingerprint. Skipping diagnostic cycle.")
                continue

            # Call run_diagnostics with all required arguments
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
                result["network_id"] = network_id
                save_run(result)

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
