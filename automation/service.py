import time
from automation.runner import run_truth_cycle

INTERVAL_SECONDS = 60  # start with 60s (we can tune later)


def start_service():
    print("[L5] U-ITE Truth Service started.")
    print(f"[L5] Interval: {INTERVAL_SECONDS} seconds")

    while True:
        try:
            run_truth_cycle()
        except Exception as e:
            print(f"[L5][ERROR] {e}")

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    start_service()
