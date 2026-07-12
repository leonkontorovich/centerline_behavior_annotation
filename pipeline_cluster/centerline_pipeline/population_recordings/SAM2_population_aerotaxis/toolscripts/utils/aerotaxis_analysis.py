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

# continuous per-frame features suitable for transition-triggered averaging
FEATURES = ["Forward_Velocity", "Reversal_Active", "Turn_Active", "Bend_Frequency", "Bend_Amplitude"]
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
def per_state_summary(df, by=("Condition", "O2_State"), fps=10.0):
    """
    Mean behaviour per gas state (and condition). Reversal_Active / Turn_Active
    are 0/1 so their means are fractions of time spent in that state.
    Bend metrics and reversal-onset rate are included when present.
    """
    by = list(by)
    g = df.groupby(by)
    agg = dict(
        mean_forward_velocity=("Forward_Velocity", "mean"),
        reversal_fraction=("Reversal_Active", "mean"),
        turn_fraction=("Turn_Active", "mean"),
        n_frames=("Frame", "size"),
    )
    if "Bend_Frequency" in df:
        agg["mean_bend_frequency_hz"] = ("Bend_Frequency", "mean")
    if "Reversal_Onset" in df:
        agg["reversal_onsets"] = ("Reversal_Onset", "sum")
    out = g.agg(**agg).reset_index()
    out["n_crops"] = g[GROUP_KEYS[-1]].nunique().values
    if "reversal_onsets" in out:
        # onsets per minute of observation in that state
        out["reversal_onsets_per_min"] = out["reversal_onsets"] / (out["n_frames"] / fps / 60.0)
    return out


def reversal_reaction(df, to_state, window_s=15.0, fps=10.0):
    """
    Reversal reaction to a gas shift: for every transition INTO `to_state`
    (e.g. the 21% O2 pulse onset), per crop, measure the latency (s) from the
    shift to the first reversal onset within `window_s`. Generalises the
    LED-specific curvature/src/rev_reaction.py to the config-driven protocol.

    Returns one tidy row per (crop, transition):
        [<GROUP_KEYS>, Time_Seconds, latency_s, reacted]
    latency_s is NaN when no reversal onset occurs within the window (reacted=0).
    """
    if "Reversal_Onset" not in df:
        raise KeyError("Reversal_Onset column required (re-run the extractor).")
    win_f = int(round(window_s * fps))
    trans = find_transitions(df)
    trans = trans[trans.to_state == to_state]

    rows = []
    for keys, sub in df.groupby(GROUP_KEYS, sort=False):
        sub = sub.sort_values("Frame").reset_index(drop=True)
        onset_frames = sub.loc[sub.Reversal_Onset == 1, "Frame"].to_numpy()
        key_dict = dict(zip(GROUP_KEYS, keys if isinstance(keys, tuple) else (keys,)))
        ev = trans
        for k, v in key_dict.items():
            ev = ev[ev[k] == v]
        for _, e in ev.iterrows():
            f0 = e["Frame"]
            after = onset_frames[(onset_frames >= f0) & (onset_frames <= f0 + win_f)]
            latency = (after[0] - f0) / fps if len(after) else np.nan
            rows.append({**key_dict, "Time_Seconds": e["Time_Seconds"],
                         "latency_s": latency, "reacted": int(len(after) > 0)})
    return pd.DataFrame(rows)


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
    ap.add_argument("--pulse_state", default=None,
                    help="gas state whose onset triggers the reversal-reaction analysis, e.g. 21pct_O2")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_results(args.results)
    print(f"Loaded {len(df):,} rows, {df.groupby(GROUP_KEYS).ngroups} crops, "
          f"states={sorted(df.O2_State.unique())}")

    summary = per_state_summary(df, fps=args.fps)
    summary.to_csv(outdir / "per_state_summary.csv", index=False)
    print(summary.to_string(index=False))

    # transition-triggered averages for every continuous feature present + populated
    ttas = {}
    for feat in ["Forward_Velocity", "Bend_Frequency", "Reversal_Active"]:
        if feat in df and df[feat].notna().any():
            t = transition_triggered_average(df, feature=feat, pre_s=args.pre_s,
                                             post_s=args.post_s, fps=args.fps)
            t.to_csv(outdir / f"transition_triggered_{feat.lower()}.csv", index=False)
            ttas[feat] = t

    # reversal reaction to the pulse onset (generalises rev_reaction.py)
    if args.pulse_state and "Reversal_Onset" in df:
        rr = reversal_reaction(df, to_state=args.pulse_state, fps=args.fps)
        rr.to_csv(outdir / "reversal_reaction.csv", index=False)
        if len(rr):
            print(f"\nReversal reaction to {args.pulse_state} onset: "
                  f"{rr.reacted.mean()*100:.0f}% reacted, "
                  f"median latency {rr.latency_s.median():.2f}s")

    # figures (best-effort; skip if plotting libs unavailable)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        metrics = [m for m in ["mean_forward_velocity", "reversal_fraction", "turn_fraction",
                               "mean_bend_frequency_hz", "reversal_onsets_per_min"] if m in summary]
        fig, axes = plt.subplots(1, len(metrics), figsize=(4 * len(metrics), 4))
        for ax, m in zip(np.atleast_1d(axes), metrics):
            plot_per_state_summary(summary, metric=m, ax=ax)
        fig.tight_layout()
        fig.savefig(outdir / "per_state_summary.png", dpi=150)

        for feat, t in ttas.items():
            if len(t):
                fig2, ax2 = plt.subplots(figsize=(8, 4))
                plot_transition_triggered(t, feature=feat, ax=ax2)
                fig2.tight_layout()
                fig2.savefig(outdir / f"transition_triggered_{feat.lower()}.png", dpi=150)
        print(f"Wrote summaries + figures to {outdir}/")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] plotting skipped ({e}); CSV summaries still written to {outdir}/")


if __name__ == "__main__":
    main()
