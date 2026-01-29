import sys
from pathlib import Path

# ==========================================================
# [BOOTSTRAP] Temporary path fix for local development
# NOTE: This will be removed once the project is packaged
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

# ==========================================================
# [IMPORTS]
# ==========================================================

from visualization.queries import fetch_all_runs_df
from visualization.plots import generate_all_plots

# ==========================================================
# [CONFIG]
# ==========================================================

OUTPUT_DIR = PROJECT_ROOT / "reports" / "charts"


def main():
    """
    Layer 4: Visualization & Insights
    --------------------------------
    1. Load diagnostic history from storage
    2. Prepare data for visualization
    3. Generate charts for network health analysis
    """
    print("--- U-ITE Layer 4: Visualization & Insights ---")

    # --------------------------------------------------
    # 1. Fetch data
    # --------------------------------------------------
    df = fetch_all_runs_df()

    if df is None or df.empty:
        print("No diagnostic data available.")
        print(f"Expected database path: {PROJECT_ROOT / 'data' / 'u_ite.db'}")
        print("Please run Layer 3 diagnostics first.")
        return

    print(f"[INFO] Loaded {len(df)} diagnostic records.")

    # --------------------------------------------------
    # 2. Data preparation
    # --------------------------------------------------
    # Keep full dataset for verdict distribution
    df_all = df.copy()

    # Clean dataset only for quality metrics (latency/loss)
    df_quality = df.dropna(subset=["latency_ms", "loss_pct"])

    dropped = len(df_all) - len(df_quality)
    if dropped > 0:
        print(f"[WARN] {dropped} records lack quality metrics (expected for outages).")

    if df_quality.empty:
        print("[ERROR] No valid quality data available for plotting.")
        return

    # --------------------------------------------------
    # 3. Generate plots
    # --------------------------------------------------
    generate_all_plots(df_quality, OUTPUT_DIR)

    print(f"[INFO] Charts saved to: {OUTPUT_DIR.resolve()}")
    print("---------------------------------------------------")


if __name__ == "__main__":
    main()
