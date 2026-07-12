#!/usr/bin/env python3
"""
Reusable temporal-analysis helpers for the aerotaxis (global gas-shift) pipeline.

Operates on the tidy per-frame table produced by create_results_dict_server.py
(aerotaxis_results.{parquet,csv,pkl}) with columns:
    Condition, Recording, Crop_ID, Frame, Time_Seconds, O2_State,
    Forward_Velocity, Reversal_Active, Turn_Active

Everything here is plain Pandas / Seaborn so it drops straight into a notebook,
a script, or an R hand-off (the summary tables are tidy CSVs).

Adapted from the reusable scaffolding of the old chemotaxis grouped notebook
(population aggregation + per-crop viewing), but reframed around temporal state
locked to global gas shifts instead of spatial gradients.

CLI:
    python aerotaxis_analysis.py aerotaxis_results.parquet --outdir analysis
produces per-state summary + gas-transition-triggered averages as CSV + PNG.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["Forward_Velocity", "Reversal_Active", "Turn_Active"]
GROUP_KEYS = ["Condition", "Recording", "Crop_ID"]


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------
def load_results(path):
    """
    Load the tidy results table.

    `path` may be a combined results file (.parquet/.csv/.pkl) OR a dataset
    folder, in which case every */output/temporal_features.csv is concatenated
    (Condition/Recording recovered from the folder tree).
    """
    path = Path(path)
    if path.is_file():
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        if path.suffix == ".csv":
            return pd.read_csv(path)
        if path.suffix in (".pkl", ".pickle"):
            return pd.read_pickle(path)
        raise ValueError(f"Unsupported results file type: {path.suffix}")

    # directory: scan per-crop CSVs
    frames = []
    for csv in sorted(path.rglob("*/output/temporal_features.csv")):
        df = pd.read_csv(csv)
        crop_dir = csv.parents[1]
        df.insert(0, "Recording", crop_dir.parent.name)
        df.insert(0, "Condition", crop_dir.parent.parent.name)
        frames.append(df)
    if not frames:
        raise SystemExit(f"No temporal_features.csv found under {path}")
    return pd.concat(frames, ignore_index=True)


# ----------------------------------------------------------------------
# Per-state summary (reversal / turn rates + mean speed per O2 state)
# ----------------------------------------------------------------------
def per_state_summary(df, by=("Condition", "O2_State")):
    """
    Mean behaviour per gas state (and condition). Reversal_Active / Turn_Active
    are 0/1 so their means are fractions of time spent in that state.
    """
    by = list(by)
    g = df.groupby(by)
    out = g.agg(
        mean_forward_velocity=("Forward_Velocity", "mean"),
        reversal_fraction=("Reversal_Active", "mean"),
        turn_fraction=("Turn_Active", "mean"),
        n_frames=("Frame", "size"),
    ).reset_index()
    out["n_crops"] = g[GROUP_KEYS[-1]].nunique().values
    return out


# ----------------------------------------------------------------------
# Gas-transition-triggered averages (the core aerotaxis analysis)
# ----------------------------------------------------------------------
def find_transitions(df):
    """
    Per crop, find frames where O2_State changes. Returns a DataFrame with one
    row per transition: [<GROUP_KEYS>, Frame, Time_Seconds, from_state, to_state].
    """
    rows = []
    for keys, sub in df.groupby(GROUP_KEYS, sort=False):
        sub = sub.sort_values("Frame")
        state = sub["O2_State"].to_numpy()
        change = np.where(state[1:] != state[:-1])[0] + 1  # index of first frame of new state
        for i in change:
            row = dict(zip(GROUP_KEYS, keys if isinstance(keys, tuple) else (keys,)))
            row.update(
                Frame=int(sub["Frame"].iloc[i]),
                Time_Seconds=float(sub["Time_Seconds"].iloc[i]),
                from_state=state[i - 1],
                to_state=state[i],
            )
            rows.append(row)
    return pd.DataFrame(rows)


def transition_triggered_average(df, feature="Forward_Velocity",
                                 pre_s=10.0, post_s=30.0, fps=10.0,
                                 transition=None):
    """
    Align `feature` to gas transitions and return a long tidy DataFrame with a
    relative-time axis (t=0 at the transition), suitable for seaborn.lineplot
    (which will show mean +/- 95% CI across crops).

    transition: optional "from->to" filter, e.g. "7pct_O2->21pct_O2".
    """
    pre_f, post_f = int(round(pre_s * fps)), int(round(post_s * fps))
    rel_time = np.arange(-pre_f, post_f + 1) / fps
    trans = find_transitions(df)
    if transition is not None:
        f, t = transition.split("->")
        trans = trans[(trans.from_state == f) & (trans.to_state == t)]

    # index each crop's series by Frame for fast slicing
    records = []
    for keys, sub in df.groupby(GROUP_KEYS, sort=False):
        sub = sub.sort_values("Frame")
        s = sub.set_index("Frame")[feature]
        key_dict = dict(zip(GROUP_KEYS, keys if isinstance(keys, tuple) else (keys,)))
        ev = trans
        for k, v in key_dict.items():
            ev = ev[ev[k] == v]
        for _, e in ev.iterrows():
            f0 = e["Frame"]
            window = s.reindex(range(f0 - pre_f, f0 + post_f + 1))
            rec = pd.DataFrame({
                "rel_time_s": rel_time,
                feature: window.to_numpy(),
                "transition": f"{e['from_state']}->{e['to_state']}",
                **key_dict,
            })
            records.append(rec)
    if not records:
        return pd.DataFrame(columns=["rel_time_s", feature, "transition", *GROUP_KEYS])
    return pd.concat(records, ignore_index=True)


# ----------------------------------------------------------------------
# Plot helpers (seaborn optional -- imported lazily so import is cheap)
# ----------------------------------------------------------------------
def plot_per_state_summary(summary, metric="reversal_fraction", ax=None):
    import seaborn as sns
    import matplotlib.pyplot as plt
    ax = ax or plt.gca()
    sns.barplot(data=summary, x="O2_State", y=metric, hue="Condition", ax=ax)
    ax.set_title(f"{metric} by gas state")
    return ax


def plot_transition_triggered(tta, feature="Forward_Velocity", ax=None):
    import seaborn as sns
    import matplotlib.pyplot as plt
    ax = ax or plt.gca()
    sns.lineplot(data=tta, x="rel_time_s", y=feature, hue="transition",
                 errorbar=("ci", 95), ax=ax)
    ax.axvline(0, color="k", ls="--", lw=1, alpha=0.6)
    ax.set_xlabel("time relative to gas shift (s)")
    ax.set_title(f"{feature} locked to gas shift")
    return ax


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", help="aerotaxis_results.{parquet,csv,pkl} or a dataset folder")
    ap.add_argument("--outdir", default="analysis")
    ap.add_argument("--fps", type=float, default=10.0)
    ap.add_argument("--pre_s", type=float, default=10.0)
    ap.add_argument("--post_s", type=float, default=30.0)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_results(args.results)
    print(f"Loaded {len(df):,} rows, {df.groupby(GROUP_KEYS).ngroups} crops, "
          f"states={sorted(df.O2_State.unique())}")

    summary = per_state_summary(df)
    summary.to_csv(outdir / "per_state_summary.csv", index=False)
    print(summary.to_string(index=False))

    tta = transition_triggered_average(
        df, feature="Forward_Velocity", pre_s=args.pre_s, post_s=args.post_s, fps=args.fps
    )
    tta.to_csv(outdir / "transition_triggered_forward_velocity.csv", index=False)

    # figures (best-effort; skip if plotting libs unavailable)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(16, 4))
        for ax, m in zip(axes, ["mean_forward_velocity", "reversal_fraction", "turn_fraction"]):
            plot_per_state_summary(summary, metric=m, ax=ax)
        fig.tight_layout()
        fig.savefig(outdir / "per_state_summary.png", dpi=150)

        if len(tta):
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            plot_transition_triggered(tta, ax=ax2)
            fig2.tight_layout()
            fig2.savefig(outdir / "transition_triggered_forward_velocity.png", dpi=150)
        print(f"Wrote summaries + figures to {outdir}/")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] plotting skipped ({e}); CSV summaries still written to {outdir}/")


if __name__ == "__main__":
    main()
