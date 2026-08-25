#!/usr/bin/env python3
"""
Generate publication-quality, modern, professional figures for aerotaxis
population behavior datasets.

Outputs:
  - per_state_summary.png: 5-panel grouped comparison (7% O2 vs 21% O2) across all genotypes
  - transition_triggered_forward_velocity.png: 2-panel upshift & downshift speed curves
  - transition_triggered_reversal_active.png: 2-panel reversal avoidance dynamics
  - transition_triggered_bend_frequency.png: 2-panel body bend frequency dynamics
  - habituation_forward_velocity.png: 10-pulse adaptation trajectory
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ----------------------------------------------------------------------
# Style & Color Palette Configuration
# ----------------------------------------------------------------------
STRAIN_PALETTE = {
    "N2": "#7FB3D5",
    "rde-4(db2038)": "#D3928F",
    "rde-4(db2036)": "#D3928F",
    "rde-4": "#D3928F",
    "npr-1(ad609)": "#3A75A4",
    "rde-4(db2039); npr-1(ad609)": "#D55E00",
    "rde-4(ne299);npr-1(ad609)": "#D55E00",
    "rde-4;npr-1": "#D55E00",
    "mut-16(pk710)": "#408468",
    "mut-16": "#408468",
}

CONDITION_ORDER = [
    "N2",
    "rde-4(db2038)",
    "mut-16(pk710)",
    "npr-1(ad609)",
    "rde-4(db2039); npr-1(ad609)",
]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.2,
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
    "legend.fontsize": 9.5,
    "legend.title_fontsize": 10.5,
})


def format_condition_label(c: str) -> str:
    """Format condition string with clean label."""
    if c == "N2":
        return "N2 (WT)"
    return c


# ----------------------------------------------------------------------
# 1. Per-State Summary (5-Panel Grouped Comparison)
# ----------------------------------------------------------------------
def generate_per_state_summary(summary_csv: Path, outpath: Path):
    if not summary_csv.exists():
        return
    df = pd.read_csv(summary_csv)
    
    # Filter for standard states
    states = ["7pct_O2", "21pct_O2"]
    df = df[df["O2_State"].isin(states)].copy()
    
    conditions = [c for c in CONDITION_ORDER if c in df["Condition"].unique()]
    if not conditions:
        conditions = sorted(df["Condition"].unique())
        
    metrics = [
        ("mean_forward_run_speed", "Forward Run Speed (mm/s)", "Run Speed (mm/s)"),
        ("mean_crawling_speed", "Absolute Crawling Speed (mm/s)", "Speed (mm/s)"),
        ("reversal_fraction", "Reversal Probability", "P(Reversal)"),
        ("turn_fraction", "Turn Probability", "P(Turn)"),
        ("mean_bend_frequency_hz", "Bend Frequency (Hz)", "Frequency (Hz)"),
        ("mean_forward_velocity", "Net Signed Velocity (mm/s)", "Velocity (mm/s)"),
    ]
    metrics = [m for m in metrics if m[0] in df.columns]
    
    fig, axes = plt.subplots(1, len(metrics), figsize=(3.8 * len(metrics), 4.2), sharey=False)
    if len(metrics) == 1:
        axes = [axes]
        
    bar_width = 0.15
    x_positions = np.array([0, 1.2])  # 7% vs 21%
    
    for ax, (m_col, m_title, m_ylabel) in zip(axes, metrics):
        for i, cond in enumerate(conditions):
            cond_data = df[df["Condition"] == cond].set_index("O2_State")
            color = STRAIN_PALETTE.get(cond, "#888888")
            
            y_vals = []
            y_errs = []
            for s in states:
                if s in cond_data.index:
                    y_vals.append(cond_data.loc[s, m_col])
                    sem_col = f"{m_col}_sem"
                    y_errs.append(cond_data.loc[s, sem_col] if sem_col in cond_data.columns else 0.0)
                else:
                    y_vals.append(np.nan)
                    y_errs.append(0.0)
                    
            offset = (i - (len(conditions) - 1) / 2) * bar_width
            bars = ax.bar(x_positions + offset, y_vals, width=bar_width * 0.92,
                          yerr=y_errs, capsize=3.5, color=color, edgecolor="#222222",
                          linewidth=0.8, label=format_condition_label(cond), alpha=0.9)
            
        ax.set_xticks(x_positions)
        ax.set_xticklabels(["7% O2\n(Baseline)", "21% O2\n(Pulse)"], fontweight="bold", fontsize=10.5)
        ax.set_ylabel(m_ylabel, fontweight="bold", fontsize=10.5)
        ax.set_title(m_title, fontweight="bold", fontsize=11.5, pad=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        ax.set_axisbelow(True)
        
    # Shared top legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.08),
               ncol=min(len(conditions), 5), frameon=False, fontsize=10)
               
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 2. Transition Dynamics (2-Panel Figure per Continuous Feature)
# ----------------------------------------------------------------------
def generate_transition_figure(csv_path: Path, feature_name: str, y_label: str,
                               title_prefix: str, outpath: Path):
    if not csv_path.exists():
        return
    df = pd.read_csv(csv_path)
    if "Condition" not in df or "transition" not in df:
        return
        
    conditions = [c for c in CONDITION_ORDER if c in df["Condition"].unique()]
    if not conditions:
        conditions = sorted(df["Condition"].unique())
        
    trans_upshift = "7pct_O2->21pct_O2"
    trans_downshift = "21pct_O2->7pct_O2"
    
    # Check available transitions
    avail = df["transition"].unique()
    if trans_upshift not in avail and trans_downshift not in avail:
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
    
    panels = [
        (ax1, trans_upshift, "Avoidance Response (7% → 21% O2)",
         "7% O2 Baseline", "21% O2 Pulse", "#E8F4F8", "#FDE8E8"),
        (ax2, trans_downshift, "Recovery Dynamics (21% → 7% O2)",
         "21% O2 Pulse", "7% O2 Recovery", "#FDE8E8", "#E8F4F8")
    ]
    
    for ax, trans_key, panel_title, left_label, right_label, left_bg, right_bg in panels:
        sub = df[df["transition"] == trans_key]
        if sub.empty:
            ax.text(0.5, 0.5, "No Transition Data", transform=ax.transAxes, ha="center")
            continue
            
        t_min = sub["rel_time_s"].min()
        t_max = sub["rel_time_s"].max()
        
        # Shaded stimulus backgrounds
        ax.axvspan(t_min, 0, color=left_bg, alpha=0.65, zorder=0)
        ax.axvspan(0, t_max, color=right_bg, alpha=0.65, zorder=0)
        
        # Background annotations
        ax.text(0.22, 0.93, left_label, transform=ax.transAxes, ha="center",
                fontsize=9.5, fontweight="bold", color="#555555",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#CCCCCC", alpha=0.85))
        ax.text(0.78, 0.93, right_label, transform=ax.transAxes, ha="center",
                fontsize=9.5, fontweight="bold", color="#555555",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#CCCCCC", alpha=0.85))
                
        # Vertical switch line
        ax.axvline(0, color="#222222", linestyle="--", linewidth=1.2, zorder=2, alpha=0.8)
        
        # Fast analytical aggregation per condition across crops
        agg = sub.groupby(["Condition", "rel_time_s"])[feature_name].agg(["mean", "sem"]).reset_index()
        
        for cond in conditions:
            c_data = agg[agg["Condition"] == cond].sort_values("rel_time_s")
            if c_data.empty:
                continue
            color = STRAIN_PALETTE.get(cond, "#888888")
            t = c_data["rel_time_s"].to_numpy()
            y = c_data["mean"].to_numpy()
            err = c_data["sem"].to_numpy()
            err = np.nan_to_num(err, nan=0.0)
            
            ax.plot(t, y, color=color, linewidth=2.0, label=format_condition_label(cond), zorder=3)
            ax.fill_between(t, y - err, y + err, color=color, alpha=0.22, zorder=2)
            
        ax.set_xlabel("Time Relative to Gas Shift (s)", fontweight="bold", fontsize=10.5)
        ax.set_title(panel_title, fontweight="bold", fontsize=11.5, pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        ax.set_axisbelow(True)
        ax.set_xlim(t_min, t_max)
        
    ax1.set_ylabel(y_label, fontweight="bold", fontsize=11)
    
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.05),
               ncol=min(len(conditions), 5), frameon=False, fontsize=10)
               
    fig.suptitle(title_prefix, fontweight="bold", fontsize=13, y=1.08)
    fig.tight_layout()
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 3. Habituation across 10 Pulses
# ----------------------------------------------------------------------
def generate_habituation_figure(pc_csv: Path, outpath: Path):
    if not pc_csv.exists():
        return
    df = pd.read_csv(pc_csv)
    if "Condition" not in df or "Cycle_Index" not in df:
        return
        
    conditions = [c for c in CONDITION_ORDER if c in df["Condition"].unique()]
    if not conditions:
        conditions = sorted(df["Condition"].unique())
        
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    
    for cond in conditions:
        sub = df[df["Condition"] == cond].sort_values("Cycle_Index")
        if sub.empty:
            continue
        color = STRAIN_PALETTE.get(cond, "#888888")
        x = sub["Cycle_Index"] + 1  # 1-indexed pulses (Pulse 1 to 10)
        y = sub["Forward_Velocity_mean"]
        
        ax.plot(x, y, marker="o", markersize=6.5, linewidth=2.0,
                color=color, label=format_condition_label(cond), zorder=3)
                
    ax.set_xlabel("Oxygen Pulse Number (Repeated 21% O2 Pulses)", fontweight="bold", fontsize=10.5)
    ax.set_ylabel("Mean Forward Velocity (mm/s)", fontweight="bold", fontsize=10.5)
    ax.set_title("Locomotor Habituation Across Repeated Oxygen Pulses", fontweight="bold", fontsize=12, pad=10)
    ax.set_xticks(np.arange(1, 11))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
    ax.set_axisbelow(True)
    
    ax.legend(frameon=False, fontsize=9.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("analysis_dir", nargs="?", default="analysis",
                    help="Directory containing the CSV summaries (default: analysis)")
    args = ap.parse_args()
    
    outdir = Path(args.analysis_dir).resolve()
    print(f"Generating publication figures for: {outdir}\n")
    
    # 1. Per-state summary
    generate_per_state_summary(outdir / "per_state_summary.csv",
                               outdir / "per_state_summary.png")
                               
    # 2. Forward velocity transition dynamics
    generate_transition_figure(
        outdir / "transition_triggered_forward_velocity.csv",
        feature_name="Forward_Velocity",
        y_label="Forward Velocity (mm/s)",
        title_prefix="Forward Velocity Dynamics Locked to Oxygen Transitions",
        outpath=outdir / "transition_triggered_forward_velocity.png"
    )
    
    # 3. Reversal probability transition dynamics
    generate_transition_figure(
        outdir / "transition_triggered_reversal_active.csv",
        feature_name="Reversal_Active",
        y_label="Reversal Probability P(Rev)",
        title_prefix="Reversal Avoidance Dynamics Locked to Oxygen Transitions",
        outpath=outdir / "transition_triggered_reversal_active.png"
    )
    
    # 4. Bend frequency transition dynamics
    generate_transition_figure(
        outdir / "transition_triggered_bend_frequency.csv",
        feature_name="Bend_Frequency",
        y_label="Bend Frequency (Hz)",
        title_prefix="Body Bend Frequency Dynamics Locked to Oxygen Transitions",
        outpath=outdir / "transition_triggered_bend_frequency.png"
    )
    
    # 5. Habituation trajectory across 10 pulses
    generate_habituation_figure(outdir / "per_cycle_summary.csv",
                                outdir / "habituation_forward_velocity.png")


if __name__ == "__main__":
    main()
