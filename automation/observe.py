import time
import signal
import sys
import logging
from datetime import datetime
from pathlib import Path

# [COMMIT] feat: Import U-ITE core modules
# Ensure these files are in the same directory or in the Python path
try:
    from internet_truth import run_diagnostics
    import storage
except ImportError as e:
    print(f"Error: Missing core U-ITE modules. Ensure internet_truth.py and storage.py are present. ({e})")
    sys.exit(1)

# -------- Configuration --------
DEFAULT_INTERVAL = 60  # Seconds between diagnostic cycles
LOG_FILE = "u-ite-observer.log"

# [COMMIT] feat: Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("U-ITE-Observer")

# -------- State Management --------
class ObserverState:
    def __init__(self):
        self.running = True
        self.last_network_id = None

state = ObserverState()

# [COMMIT] feat: Implement graceful shutdown handler
def shutdown_handler(signum, frame):
    logger.info("Shutdown signal received. Cleaning up...")
    state.running = False

# Register signals for graceful exit
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

# -------- Core Observer Logic --------
def observe(interval=DEFAULT_INTERVAL):
    """
    Continuous U-ITE truth observer.
    Executes diagnostics, detects network changes, and persists data.
    """
    print("\n" + "="*45)
    print("  U-ITE | Continuous Truth Observer")
    print(f"  Interval: {interval} seconds")
    print(f"  Log File: {LOG_FILE}")
    print("  Press Ctrl+C to stop")
    print("="*45 + "\n")

    # [COMMIT] feat: Initialize database once at startup
    try:
        storage.init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    while state.running:
        start_time = time.time()
        
        try:
            # [COMMIT] feat: Execute Layer 1 & 2 Diagnostics
            # We assume run_diagnostics is updated to return the result dict
            result = run_diagnostics(return_result=True)

            if not result:
                logger.warning("Diagnostic cycle returned no data (No active network?).")
            else:
                network_id = result.get("network_id")
                verdict = result.get("verdict", "Unknown")
                latency = result.get("avg_latency")
                loss = result.get("packet_loss")

                # [COMMIT] feat: Detect and report network context changes
                if state.last_network_id and network_id != state.last_network_id:
                    logger.info(f"NETWORK CHANGE DETECTED: {state.last_network_id} -> {network_id}")
                
                state.last_network_id = network_id

                # [COMMIT] feat: Persist results to Layer 3 (Storage)
                storage.save_run(result)

                # [COMMIT] feat: Professional CLI Output
                status_msg = f"Verdict: {verdict}"
                if latency is not None and loss is not None:
                    status_msg += f" | Latency: {latency:.1f}ms | Loss: {loss}%"
                
                logger.info(status_msg)

        except Exception as e:
            # [COMMIT] fix: Resilient error handling to keep the loop alive
            logger.error(f"Diagnostic cycle failed: {e}", exc_info=True)

        # [COMMIT] feat: Calculate remaining sleep time to maintain fixed interval
        elapsed = time.time() - start_time
        sleep_time = max(0, interval - elapsed)
        
        # Check running flag frequently during sleep for faster shutdown response
        for _ in range(int(sleep_time)):
            if not state.running:
                break
            time.sleep(1)
        
        # Handle fractional sleep time
        if state.running:
            time.sleep(sleep_time % 1)

    logger.info("U-ITE Observer stopped.")

if __name__ == "__main__":
    # Allow interval to be passed as a command line argument
    interval = DEFAULT_INTERVAL
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid interval provided. Using default: {DEFAULT_INTERVAL}s")

    observe(interval)
