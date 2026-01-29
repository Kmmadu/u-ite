import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================================
# [CONFIG] Optional plotting style
# ==========================================================

def apply_plot_style():
    """Apply a consistent plotting style if available."""
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass


# ==========================================================
# [UTIL] Validation
# ==========================================================

def _validate_df(df: pd.DataFrame):
    if df is None or df.empty:
        raise ValueError("DataFrame is empty or None — nothing to plot.")


# ==========================================================
# [PLOTS] Latency
# ==========================================================

def plot_latency_over_time(df: pd.DataFrame, save_path: Path = None):
    """Plot average latency over time."""
    _validate_df(df)
    apply_plot_style()

    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp"], df["latency_ms"], label="Avg Latency")

    plt.axhline(
        y=50,
        linestyle="--",
        alpha=0.6,
        label="50 ms threshold"
    )

    plt.title("Average Network Latency Over Time")
    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


# ==========================================================
# [PLOTS] Packet Loss
# ==========================================================

def plot_loss_over_time(df: pd.DataFrame, save_path: Path = None):
    """Plot packet loss percentage over time."""
    _validate_df(df)
    apply_plot_style()

    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp"], df["loss_pct"], label="Packet Loss (%)")

    plt.axhline(
        y=1,
        linestyle="--",
        alpha=0.6,
        label="1% threshold"
    )

    plt.title("Packet Loss Over Time")
    plt.xlabel("Time")
    plt.ylabel("Packet Loss (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


# ==========================================================
# [PLOTS] Verdict Distribution
# ==========================================================

def plot_verdict_distribution(df: pd.DataFrame, save_path: Path = None):
    """Plot distribution of diagnostic verdicts."""
    _validate_df(df)
    apply_plot_style()

    verdict_counts = df["verdict"].value_counts()

    colors = {
        "Healthy": "#2ca02c",
        "Degraded Internet": "#ff7f0e",
        "ISP Failure": "#d62728",
        "DNS Failure": "#9467bd",
        "Local Network Failure": "#1f77b4",
        "Application Failure": "#8c564b"
    }

    plot_colors = [colors.get(v, "#7f7f7f") for v in verdict_counts.index]

    plt.figure(figsize=(8, 8))
    plt.pie(
        verdict_counts,
        labels=verdict_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=plot_colors,
        wedgeprops={"edgecolor": "black"}
    )

    plt.title("Network Diagnostic Verdict Distribution")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()


# ==========================================================
# [ENTRY] Generate all plots
# ==========================================================

def generate_all_plots(df: pd.DataFrame, output_dir: Path):
    """Generate and save all Layer-4 plots."""
    _validate_df(df)

    output_dir.mkdir(parents=True, exist_ok=True)

    plot_latency_over_time(df, output_dir / "latency_over_time.png")
    plot_loss_over_time(df, output_dir / "loss_over_time.png")
    plot_verdict_distribution(df, output_dir / "verdict_distribution.png")

    print(f"[INFO] Generated plots in {output_dir}")
