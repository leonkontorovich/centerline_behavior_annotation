#!/usr/bin/env python3
"""
Advanced Publication-Grade Behavioral Figures for Aerotaxis Population Analysis.

Generates:
  1. genetic_interaction_analysis.png: 2x2 Factorial Reaction Norm & Epistasis Plots
  2. sensory_reversal_latency_ecdf.png: Reversal Reaction Kinetics & eCDF Survival
  3. behavioral_state_ethogram.png: Behavioral State Budget (Forward, Reversal, Turn)
  4. locomotor_gait_phase_space.png: Biomechanical Phase Space (Speed vs Bend Frequency)
  5. superplots_plate_replicates.png: SuperPlots (Crop Distributions + Plate Means)
  6. full_protocol_continuous_timeseries.png: Whole-Assay 10-Pulse Timeline
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
    if c == "N2":
        return "N2 (WT)"
    return c


# ----------------------------------------------------------------------
# 1. Genetic Interaction / 2x2 Factorial Epistasis Plot
# ----------------------------------------------------------------------
def plot_genetic_interaction(df: pd.DataFrame, outdir: Path):
    """
    2x2 Factorial Epistasis:
      Backgrounds: WT (ZIM2521) vs npr-1 (ZIM2554)
      Alleles: WT vs rde-4
    """
    # Plate-level means for 2x2 comparison
    states = ["7pct_O2", "21pct_O2"]
    sub = df[df["O2_State"].isin(states)].copy()
    
    # Add speed definitions
    sub["_abs_speed"] = sub["Forward_Velocity"].abs()
    sub["_fwd_run_speed"] = sub["Forward_Velocity"].where((sub["Reversal_Active"] == 0) & (sub["Turn_Active"] == 0) & (sub["Forward_Velocity"] > 0), np.nan)
    
    # Calculate plate means
    plate_means = sub.groupby(["Condition", "Recording", "O2_State"], observed=True).agg({
        "Forward_Velocity": "mean",
        "_abs_speed": "mean",
        "_fwd_run_speed": "mean",
        "Reversal_Active": "mean",
        "Bend_Frequency": "mean",
    }).reset_index()
    
    # Pivot state to calculate deltas
    piv_fwd = plate_means.pivot(index=["Condition", "Recording"], columns="O2_State", values="_fwd_run_speed").reset_index()
    piv_fwd["delta_fwd_speed"] = piv_fwd["21pct_O2"] - piv_fwd["7pct_O2"]
    
    piv_rev = plate_means.pivot(index=["Condition", "Recording"], columns="O2_State", values="Reversal_Active").reset_index()
    piv_freq = plate_means.pivot(index=["Condition", "Recording"], columns="O2_State", values="Bend_Frequency").reset_index()
    
    fig, axes = plt.subplots(1, 4, figsize=(15.5, 4.4))
    
    # Map conditions to 2x2 grid
    mapping = {
        "N2": (0, "WT rde-4(+)"),
        "rde-4(db2038)": (0, "rde-4(db2038)"),
        "npr-1(ad609)": (1, "WT rde-4(+)"),
        "rde-4(db2039); npr-1(ad609)": (1, "rde-4(db2039)"),
    }
    
    panels = [
        (axes[0], piv_fwd, "21pct_O2", "Forward Run Speed (21% O2)", "Run Speed (mm/s)"),
        (axes[1], piv_fwd, "delta_fwd_speed", "Speed Surge (Δ 21% - 7% O2)", "Δ Run Speed (mm/s)"),
        (axes[2], piv_freq, "21pct_O2", "Bend Frequency (21% O2)", "Frequency (Hz)"),
        (axes[3], piv_rev, "21pct_O2", "Reversal Avoidance (21% O2)", "P(Reversal)"),
    ]
    
    for ax, data_df, col_name, title, ylabel in panels:
        # Compute group means and SEMs
        means = data_df.groupby("Condition", observed=True)[col_name].mean()
        sems = data_df.groupby("Condition", observed=True)[col_name].sem()
        
        # Plot individual plate dots with slight jitter
        for cond, (x_bg, allele_type) in mapping.items():
            if cond not in data_df["Condition"].values:
                continue
            cond_data = data_df[data_df["Condition"] == cond][col_name].dropna()
            jitter = (np.random.RandomState(42).rand(len(cond_data)) - 0.5) * 0.12
            x_pos = x_bg + (-0.08 if "WT" in allele_type else 0.08)
            color = STRAIN_PALETTE.get(cond, "#888888")
            ax.scatter(np.full_like(cond_data, x_pos) + jitter, cond_data,
                       color=color, alpha=0.5, s=28, edgecolors="none", zorder=2)
            
        # Draw interaction lines
        # Line 1: rde-4(+) (N2 -> npr-1)
        if "N2" in means and "npr-1(ad609)" in means:
            ax.plot([0 - 0.08, 1 - 0.08], [means["N2"], means["npr-1(ad609)"]],
                    color="#3A75A4", linewidth=2.2, marker="o", markersize=7,
                    label="rde-4(+)", zorder=3)
            ax.errorbar([0 - 0.08, 1 - 0.08], [means["N2"], means["npr-1(ad609)"]],
                        yerr=[sems["N2"], sems["npr-1(ad609)"]],
                        fmt="none", ecolor="#3A75A4", elinewidth=1.8, capsize=4, zorder=3)
            
        # Line 2: rde-4 mutant (rde-4 -> rde-4;npr-1)
        if "rde-4(db2038)" in means and "rde-4(db2039); npr-1(ad609)" in means:
            ax.plot([0 + 0.08, 1 + 0.08], [means["rde-4(db2038)"], means["rde-4(db2039); npr-1(ad609)"]],
                    color="#D55E00", linewidth=2.2, marker="s", markersize=7,
                    label="rde-4(mut)", zorder=3)
            ax.errorbar([0 + 0.08, 1 + 0.08], [means["rde-4(db2038)"], means["rde-4(db2039); npr-1(ad609)"]],
                        yerr=[sems["rde-4(db2038)"], sems["rde-4(db2039); npr-1(ad609)"]],
                        fmt="none", ecolor="#D55E00", elinewidth=1.8, capsize=4, zorder=3)
            
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["WT\n(Solitary)", "npr-1(ad609)\n(Social / Aerotactic)"], fontweight="bold")
        ax.set_ylabel(ylabel, fontweight="bold", fontsize=10.5)
        ax.set_title(title, fontweight="bold", fontsize=11, pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        ax.set_axisbelow(True)
        ax.set_xlim(-0.35, 1.35)
        
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.08),
               ncol=2, frameon=False, fontsize=10.5)
               
    fig.suptitle("Genetic Epistasis & Interaction Analysis (rde-4 × npr-1)", fontweight="bold", fontsize=13, y=1.14)
    fig.tight_layout()
    outpath = outdir / "genetic_interaction_analysis.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 2. Sensory Reversal Latency & Reaction Kinetics (eCDF)
# ----------------------------------------------------------------------
def plot_reversal_latency_ecdf(df: pd.DataFrame, rev_csv: Path, outdir: Path):
    if not rev_csv.exists():
        return
    rr = pd.read_csv(rev_csv)
    
    conditions = [c for c in CONDITION_ORDER if c in rr["Condition"].unique()]
    if not conditions:
        conditions = sorted(rr["Condition"].unique())
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6))
    
    # Panel A: eCDF of latency for animals that reacted within 15s
    for cond in conditions:
        sub = rr[(rr["Condition"] == cond) & (rr["reacted"] == 1)]
        if sub.empty:
            continue
        latencies = np.sort(sub["latency_s"].dropna().to_numpy())
        ecdf = np.arange(1, len(latencies) + 1) / len(latencies)
        color = STRAIN_PALETTE.get(cond, "#888888")
        ax1.step(latencies, ecdf, where="post", color=color, linewidth=2.2,
                 label=f"{format_condition_label(cond)} (med={np.median(latencies):.2f}s)")
        
    ax1.set_xlabel("Reversal Latency (s) from 21% O2 Onset", fontweight="bold", fontsize=10.5)
    ax1.set_ylabel("Cumulative Fraction of Responders", fontweight="bold", fontsize=10.5)
    ax1.set_title("Reversal Reaction Latency Kinetics (eCDF)", fontweight="bold", fontsize=11.5, pad=8)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
    ax1.set_xlim(0, 15)
    ax1.set_ylim(0, 1.02)
    ax1.legend(frameon=False, fontsize=9.0, loc="lower right")
    
    # Panel B: Plate-level Reaction Probability vs Median Latency
    plate_reac = rr.groupby(["Condition", "Recording"], observed=True).agg(
        reacted_frac=("reacted", "mean"),
        med_latency=("latency_s", "median")
    ).reset_index()
    
    for cond in conditions:
        p_sub = plate_reac[plate_reac["Condition"] == cond]
        if p_sub.empty:
            continue
        color = STRAIN_PALETTE.get(cond, "#888888")
        ax2.scatter(p_sub["med_latency"], p_sub["reacted_frac"] * 100,
                    color=color, s=65, edgecolors="#222222", linewidth=0.8,
                    label=format_condition_label(cond), alpha=0.85)
        
    ax2.set_xlabel("Plate Median Latency (s)", fontweight="bold", fontsize=10.5)
    ax2.set_ylabel("Plate Responders (% Reacted)", fontweight="bold", fontsize=10.5)
    ax2.set_title("Plate Sensory Avoidance Reliability", fontweight="bold", fontsize=11.5, pad=8)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
    ax2.xaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
    ax2.set_ylim(80, 102)
    ax2.legend(frameon=False, fontsize=9.0, loc="lower left")
    
    fig.suptitle("Sensory Transduction Kinetics Upon 21% O2 Shift", fontweight="bold", fontsize=13, y=1.06)
    fig.tight_layout()
    outpath = outdir / "sensory_reversal_latency_ecdf.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 3. Behavioral State Budget Ethogram (Forward vs Reversal vs Turn)
# ----------------------------------------------------------------------
def plot_behavioral_state_ethogram(df: pd.DataFrame, outdir: Path):
    """
    100% Stacked Bar Ethogram:
      Reversal Active (Rev)
      Turn Active (Omega / Turn)
      Pure Forward Crawling (1 - Rev - Turn)
    """
    states = ["7pct_O2", "21pct_O2"]
    sub = df[df["O2_State"].isin(states)].copy()
    
    # Calculate state fractions
    sub["is_reversal"] = sub["Reversal_Active"] == 1
    sub["is_turn"] = (sub["Turn_Active"] == 1) & (sub["Reversal_Active"] == 0)
    sub["is_forward"] = (sub["Reversal_Active"] == 0) & (sub["Turn_Active"] == 0)
    
    etho = sub.groupby(["Condition", "O2_State"], observed=True)[["is_forward", "is_reversal", "is_turn"]].mean().reset_index()
    
    conditions = [c for c in CONDITION_ORDER if c in etho["Condition"].unique()]
    if not conditions:
        conditions = sorted(etho["Condition"].unique())
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
    
    panels = [
        (ax1, "7pct_O2", "Behavioral Budget: 7% O2 (Baseline)"),
        (ax2, "21pct_O2", "Behavioral Budget: 21% O2 (Avoidance Pulse)")
    ]
    
    state_colors = {
        "is_forward": "#4A90E2",   # Forward Crawling (Blue)
        "is_reversal": "#E74C3C",  # Reversals (Red)
        "is_turn": "#F39C12",      # Turns (Amber/Orange)
    }
    
    for ax, o2_state, title in panels:
        s_data = etho[etho["O2_State"] == o2_state].set_index("Condition")
        
        y_pos = np.arange(len(conditions))
        fwd_vals = [s_data.loc[c, "is_forward"] * 100 if c in s_data.index else 0 for c in conditions]
        rev_vals = [s_data.loc[c, "is_reversal"] * 100 if c in s_data.index else 0 for c in conditions]
        turn_vals = [s_data.loc[c, "is_turn"] * 100 if c in s_data.index else 0 for c in conditions]
        
        # Stacked horizontal bars
        ax.barh(y_pos, fwd_vals, color=state_colors["is_forward"], edgecolor="#222222",
                linewidth=0.8, label="Forward Crawling", alpha=0.9)
        ax.barh(y_pos, rev_vals, left=fwd_vals, color=state_colors["is_reversal"], edgecolor="#222222",
                linewidth=0.8, label="Reversals", alpha=0.9)
        ax.barh(y_pos, turn_vals, left=np.array(fwd_vals) + np.array(rev_vals),
                color=state_colors["is_turn"], edgecolor="#222222",
                linewidth=0.8, label="Omega Bends / Turns", alpha=0.9)
                
        ax.set_yticks(y_pos)
        ax.set_yticklabels([format_condition_label(c) for c in conditions], fontweight="bold", fontsize=10)
        ax.set_xlabel("Fraction of Time Budget (%)", fontweight="bold", fontsize=10.5)
        ax.set_title(title, fontweight="bold", fontsize=11.5, pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlim(0, 100)
        ax.xaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        ax.invert_yaxis()
        
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.07),
               ncol=3, frameon=False, fontsize=10)
               
    fig.suptitle("Behavioral State Budget Ethogram (Time Partitioning)", fontweight="bold", fontsize=13, y=1.14)
    fig.tight_layout()
    outpath = outdir / "behavioral_state_ethogram.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 4. Biomechanical Gait / Locomotor Phase Space
# ----------------------------------------------------------------------
def plot_locomotor_gait_phase_space(df: pd.DataFrame, outdir: Path):
    """
    Locomotor Phase Space:
      Forward Velocity vs Body Bend Frequency across 7% O2 vs 21% O2.
    """
    states = ["7pct_O2", "21pct_O2"]
    sub = df[df["O2_State"].isin(states) & (df["Forward_Velocity"].notna()) & (df["Bend_Frequency"].notna())].copy()
    
    conditions = [c for c in CONDITION_ORDER if c in sub["Condition"].unique()]
    if not conditions:
        conditions = sorted(sub["Condition"].unique())
        
    fig, axes = plt.subplots(1, len(conditions), figsize=(3.3 * len(conditions), 4.2), sharey=True, sharex=True)
    if len(conditions) == 1:
        axes = [axes]
        
    for ax, cond in zip(axes, conditions):
        c_sub = sub[sub["Condition"] == cond]
        
        # 7% O2 centroid
        s7 = c_sub[c_sub["O2_State"] == "7pct_O2"]
        s21 = c_sub[c_sub["O2_State"] == "21pct_O2"]
        
        color = STRAIN_PALETTE.get(cond, "#888888")
        
        # Plot 2D mean shift vector
        x7, y7 = s7["Bend_Frequency"].mean(), s7["Forward_Velocity"].mean()
        x21, y21 = s21["Bend_Frequency"].mean(), s21["Forward_Velocity"].mean()
        
        # Error ellipses/crosses
        ax.errorbar(x7, y7, xerr=s7["Bend_Frequency"].sem()*3, yerr=s7["Forward_Velocity"].sem()*3,
                    fmt="o", color="#3A75A4", markersize=7, label="7% O2", zorder=3)
        ax.errorbar(x21, y21, xerr=s21["Bend_Frequency"].sem()*3, yerr=s21["Forward_Velocity"].sem()*3,
                    fmt="s", color="#E74C3C", markersize=7, label="21% O2", zorder=3)
                    
        # Arrow connecting state transition
        ax.annotate("", xy=(x21, y21), xytext=(x7, y7),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2.2, mutation_scale=15))
                    
        ax.set_title(format_condition_label(cond), fontweight="bold", fontsize=10.5, pad=8)
        ax.set_xlabel("Bend Frequency (Hz)", fontweight="bold", fontsize=10)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        ax.xaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        
    axes[0].set_ylabel("Forward Velocity (mm/s)", fontweight="bold", fontsize=10.5)
    
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.08),
               ncol=2, frameon=False, fontsize=10)
               
    fig.suptitle("Locomotor Gait Shift (Frequency vs Velocity)", fontweight="bold", fontsize=13, y=1.14)
    fig.tight_layout()
    outpath = outdir / "locomotor_gait_phase_space.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 5. SuperPlots: Plate Means Superimposed on Crop Distributions
# ----------------------------------------------------------------------
def plot_superplots(df: pd.DataFrame, outdir: Path):
    """
    Lord et al. (JCB 2020) SuperPlots:
      Crop fragment distributions (light) overlaid with independent plate means (bold dots)
      and true biological plate-level SEM error bars.
    """
    states = ["7pct_O2", "21pct_O2"]
    sub = df[df["O2_State"].isin(states)].copy()
    sub["_fwd_run_speed"] = sub["Forward_Velocity"].where((sub["Reversal_Active"] == 0) & (sub["Turn_Active"] == 0) & (sub["Forward_Velocity"] > 0), np.nan)
    
    # Calculate crop means
    crop_means = sub.groupby(["Condition", "Recording", "Crop_ID", "O2_State"], observed=True).agg({
        "_fwd_run_speed": "mean",
        "Forward_Velocity": "mean",
        "Reversal_Active": "mean",
    }).reset_index()
    
    # Calculate plate means
    plate_means = crop_means.groupby(["Condition", "Recording", "O2_State"], observed=True).agg({
        "_fwd_run_speed": "mean",
        "Forward_Velocity": "mean",
        "Reversal_Active": "mean",
    }).reset_index()
    
    conditions = [c for c in CONDITION_ORDER if c in crop_means["Condition"].unique()]
    if not conditions:
        conditions = sorted(crop_means["Condition"].unique())
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    
    metrics = [
        (ax1, "_fwd_run_speed", "Forward Run Speed (mm/s)", "Forward Run Speed SuperPlot"),
        (ax2, "Reversal_Active", "P(Reversal)", "Reversal Avoidance SuperPlot"),
    ]
    
    for ax, metric, ylabel, title in metrics:
        x_positions = np.arange(len(conditions))
        
        for i, cond in enumerate(conditions):
            color = STRAIN_PALETTE.get(cond, "#888888")
            
            # Crop fragment points (light jitter)
            c_data = crop_means[(crop_means["Condition"] == cond) & (crop_means["O2_State"] == "21pct_O2")][metric]
            jitter = (np.random.RandomState(i).rand(len(c_data)) - 0.5) * 0.35
            ax.scatter(np.full_like(c_data, i) + jitter, c_data,
                       color=color, alpha=0.15, s=12, edgecolors="none", zorder=1)
            
            # Plate means (bold solid dots)
            p_data = plate_means[(plate_means["Condition"] == cond) & (plate_means["O2_State"] == "21pct_O2")][metric]
            p_jitter = (np.random.RandomState(i+100).rand(len(p_data)) - 0.5) * 0.15
            ax.scatter(np.full_like(p_data, i) + p_jitter, p_data,
                       color=color, s=80, edgecolors="#111111", linewidth=1.2, zorder=3)
            
            # Grand plate mean & SEM error bar
            grand_mean = p_data.mean()
            grand_sem = p_data.sem()
            ax.errorbar(i, grand_mean, yerr=grand_sem, fmt="D", color="#111111",
                        markersize=9, elinewidth=2.2, capsize=5, zorder=4)
            
        ax.set_xticks(x_positions)
        ax.set_xticklabels([format_condition_label(c) for c in conditions], fontweight="bold", fontsize=9.5, rotation=12)
        ax.set_ylabel(ylabel, fontweight="bold", fontsize=10.5)
        ax.set_title(title + " in 21% O2", fontweight="bold", fontsize=11.5, pad=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
        ax.set_axisbelow(True)
        
    fig.suptitle("Biological SuperPlots (Crop Distributions & Independent Plate Means)", fontweight="bold", fontsize=13, y=1.04)
    fig.tight_layout()
    outpath = outdir / "superplots_plate_replicates.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
# 6. Continuous Full-Assay Whole-Protocol Timeseries Overview
# ----------------------------------------------------------------------
def plot_continuous_whole_protocol(df: pd.DataFrame, outdir: Path):
    """
    Continuous Whole-Assay Timeline across all 10 Cycles (0 to 1800s).
    """
    if "Time_Seconds" not in df:
        return
    # Bin by 2-second windows across the entire protocol
    sub = df[(df["Time_Seconds"] >= 0) & (df["Time_Seconds"] <= 1800)].copy()
    sub["time_bin"] = (sub["Time_Seconds"] // 2) * 2
    
    ts_agg = sub.groupby(["Condition", "time_bin"], observed=True).agg({
        "Forward_Velocity": "mean",
        "Reversal_Active": "mean",
        "O2_State": "first"
    }).reset_index()
    
    conditions = [c for c in CONDITION_ORDER if c in ts_agg["Condition"].unique()]
    if not conditions:
        conditions = sorted(ts_agg["Condition"].unique())
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14.5, 6.5), sharex=True)
    
    # Detect 21% O2 pulses from the data
    state_series = sub.groupby("time_bin", observed=True)["O2_State"].first()
    pulse_times = state_series[state_series == "21pct_O2"].index
    
    # Shade 21% O2 pulse intervals
    for ax in (ax1, ax2):
        in_pulse = False
        start_t = 0
        for t in sorted(state_series.index):
            st = state_series.loc[t]
            if st == "21pct_O2" and not in_pulse:
                in_pulse = True
                start_t = t
            elif st != "21pct_O2" and in_pulse:
                in_pulse = False
                ax.axvspan(start_t, t, color="#FDE8E8", alpha=0.6, zorder=0)
        if in_pulse:
            ax.axvspan(start_t, max(state_series.index), color="#FDE8E8", alpha=0.6, zorder=0)
            
    # Plot continuous traces for all 5 strains
    for cond in conditions:
        c_ts = ts_agg[ts_agg["Condition"] == cond].sort_values("time_bin")
        color = STRAIN_PALETTE.get(cond, "#888888")
        
        # Smooth with 3-bin rolling window
        y_vel = c_ts["Forward_Velocity"].rolling(3, center=True, min_periods=1).mean()
        y_rev = c_ts["Reversal_Active"].rolling(3, center=True, min_periods=1).mean()
        
        ax1.plot(c_ts["time_bin"], y_vel, color=color, linewidth=1.5, label=format_condition_label(cond))
        ax2.plot(c_ts["time_bin"], y_rev, color=color, linewidth=1.5, label=format_condition_label(cond))
        
    ax1.set_ylabel("Forward Velocity (mm/s)", fontweight="bold", fontsize=10.5)
    ax1.set_title("Full Protocol Timeline: Forward Crawling Velocity Across 10 Pulses", fontweight="bold", fontsize=11.5)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
    
    ax2.set_ylabel("P(Reversal)", fontweight="bold", fontsize=10.5)
    ax2.set_title("Full Protocol Timeline: Reversal Avoidance Probability Across 10 Pulses", fontweight="bold", fontsize=11.5)
    ax2.set_xlabel("Experiment Time (s)", fontweight="bold", fontsize=10.5)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.yaxis.grid(True, linestyle=":", alpha=0.4, color="#999999")
    ax2.set_xlim(0, 1800)
    
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.04),
               ncol=min(len(conditions), 5), frameon=False, fontsize=10)
               
    fig.tight_layout()
    outpath = outdir / "full_protocol_continuous_timeseries.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✅ Generated: {outpath}")


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("parquet_file", help="Path to aerotaxis_results.parquet")
    ap.add_argument("--outdir", default="analysis", help="Output directory")
    args = ap.parse_args()
    
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading parquet from: {args.parquet_file}...")
    df = pd.read_parquet(args.parquet_file)
    print(f"Loaded {len(df):,} rows, {df['Condition'].nunique()} conditions.\n")
    
    # Filter for alive crops if crop_qc.csv is present
    qc_file = outdir / "crop_qc.csv"
    if qc_file.exists():
        qc = pd.read_csv(qc_file)
        live_crops = set(map(tuple, qc.loc[qc["alive"], ["Condition", "Recording", "Crop_ID"]].to_numpy()))
        df = df[df.set_index(["Condition", "Recording", "Crop_ID"]).index.isin(live_crops)].reset_index(drop=True)
        print(f"Filtered to {len(df):,} motile/alive rows.")
        
    rev_csv = outdir / "reversal_reaction.csv"
    
    print("\n--- Generating Advanced Figures ---")
    plot_genetic_interaction(df, outdir)
    plot_reversal_latency_ecdf(df, rev_csv, outdir)
    plot_behavioral_state_ethogram(df, outdir)
    plot_locomotor_gait_phase_space(df, outdir)
    plot_superplots(df, outdir)
    plot_continuous_whole_protocol(df, outdir)
    print("\nAll advanced publication figures generated successfully!")


if __name__ == "__main__":
    main()
