from uite.diagnostics.base import run_diagnostics
from uite.storage.db import save_run
from visualization.dashboard import generate_charts
from utils.network import get_network_id


def run_truth_cycle():
    """
    Executes one full truth cycle:
    1. Detect network
    2. Run diagnostics
    3. Save results
    4. Generate charts if saved
    """
    print("[L5] Starting truth cycle...")

    network_id = get_network_id()
    print(f"[L5] Network ID: {network_id}")

    snapshot = run_diagnostics(network_id)

    saved = save_run(snapshot)

    if saved:
        print("[L5] Truth saved. Updating charts...")
        generate_charts()
    else:
        print("[L5] Nothing saved. Skipping charts.")
