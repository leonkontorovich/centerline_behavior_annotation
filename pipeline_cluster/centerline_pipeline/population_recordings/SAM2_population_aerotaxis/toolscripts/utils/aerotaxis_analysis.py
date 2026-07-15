#!/usr/bin/env python3
"""
Reusable temporal-analysis helpers for the aerotaxis (global gas-shift) pipeline.

Operates on the tidy per-frame table produced by create_results_dict_server.py
(aerotaxis_results.{parquet,csv,pkl}) with columns:
    Condition, Recording, Crop_ID, Frame, Time_Seconds, O2_State,
    Forward_Velocity, Reversal_Active, Turn_Active, ... , Occluded
Occluded frames (SWC-flagged animal loss) are dropped on load by default.

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
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the provenance parsing (Condition/Genotype/Recording/Plate + `_new`
# stripping) from the table builder so both agree on how folders map to columns.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from create_results_dict_server import _strip_new, parse_recording_name, DEFAULT_NAME_RE
    _NAME_RE = re.compile(DEFAULT_NAME_RE)
except Exception:  # pragma: no cover - fallback if run in isolation
    _NAME_RE = None

    def _strip_new(name):
        return name[:-4] if name.endswith("_new") else name

    def parse_recording_name(recording, name_re):
        return recording, ""

# continuous per-frame features suitable for transition-triggered averaging
FEATURES = ["Forward_Velocity", "Reversal_Active", "Turn_Active", "Bend_Frequency", "Bend_Amplitude"]
GROUP_KEYS = ["Condition", "Recording", "Crop_ID"]

# Motility QC defaults: keep only crops that are tracked long enough AND that
# actually travelled -- i.e. live, moving worms, not dead animals, debris, or
# bubbles. Non-destructive (filters the table; never deletes files) and
# duration-aware (uses integrated speed, not raw positional SD like the
# irreversible step-5 bubble filter). Tune via load_results()/CLI.
MIN_TRACK_SECONDS = 10.0   # a crop shorter than this (post-occlusion) is too brief to trust
MIN_PATH_MM = 0.5          # total distance travelled below this = didn't move (dead/bubble)


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------
def load_results(path, drop_occluded=True, require_motile=True, fps=10.0,
                 min_track_seconds=MIN_TRACK_SECONDS, min_path_mm=MIN_PATH_MM,
                 verbose=True):
    """
    Load the tidy results table.

    `path` may be a combined results file (.parquet/.csv/.pkl) OR a dataset
    folder, in which case every */output/temporal_features.csv is concatenated
    (Condition/Genotype/Recording/Plate recovered from the folder tree, with the
    setup `_new` wrapper stripped -- see create_results_dict_server).

    `drop_occluded` (default True): if the SWC-derived `Occluded` column is
    present, drop frames where the animal was lost/occluded -- their behaviour
    values come from a blank crop frame and would bias per-state means. Pass
    False to keep every frame (e.g. to inspect occlusion itself). No-op for data
    from older SWC versions that lacks the column.

    `require_motile` (default True): keep only crops that are LIVE, MOVING worms
    -- tracked for at least `min_track_seconds` and that travelled at least
    `min_path_mm` total (dead worms, debris and bubbles sit near zero). This runs
    AFTER the occlusion filter, on real frames only. See `filter_motile`. Pass
    False to keep every crop.
    """
    path = Path(path)
    if path.is_file():
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
        elif path.suffix == ".csv":
            df = pd.read_csv(path)
        elif path.suffix in (".pkl", ".pickle"):
            df = pd.read_pickle(path)
        else:
            raise ValueError(f"Unsupported results file type: {path.suffix}")
    else:
        # directory: scan per-crop CSVs, recovering provenance the same way the
        # table builder does (so the two code paths never disagree).
        frames = []
        for csv in sorted(path.rglob("*/output/temporal_features.csv")):
            d = pd.read_csv(csv)
            crop_dir = csv.parents[1]
            recording = _strip_new(crop_dir.parent.name)
            condition_raw = _strip_new(crop_dir.parents[1].name)
            genotype, plate = parse_recording_name(recording, _NAME_RE) if _NAME_RE else (recording, "")
            condition = genotype if condition_raw == recording else condition_raw
            d.insert(0, "Plate", plate)
            d.insert(0, "Recording", recording)
            d.insert(0, "Genotype", genotype)
            d.insert(0, "Condition", condition)
            frames.append(d)
        if not frames:
            raise SystemExit(f"No temporal_features.csv found under {path}")
        df = pd.concat(frames, ignore_index=True)

    df = _apply_occlusion_filter(df, drop_occluded)
    if require_motile:
        df = filter_motile(df, fps=fps, min_track_seconds=min_track_seconds,
                           min_path_mm=min_path_mm, verbose=verbose)
    return df


def _apply_occlusion_filter(df, drop_occluded):
    """Drop occluded frames if requested and the `Occluded` column exists."""
    if drop_occluded and "Occluded" in df.columns:
        return df[df["Occluded"] == 0].reset_index(drop=True)
    return df


# ----------------------------------------------------------------------
# Motility QC -- keep only live worms that moved
# ----------------------------------------------------------------------
def crop_motility(df, fps=10.0):
    """Per-crop motility summary from the (already occlusion-filtered) table.

    Returns one row per crop with:
      n_frames, duration_s, total_path_mm (integral of |Forward_Velocity|),
      mean_speed_mm_s (mean |Forward_Velocity|).
    `total_path_mm` is the distance the worm actually travelled -- a dead animal,
    a bubble, or debris sits near zero regardless of how long it was tracked,
    while a brief real track isn't penalised just for being short (that is what
    the separate duration gate is for). NaN velocities are ignored.
    """
    rows = []
    for keys, sub in df.groupby(GROUP_KEYS, sort=False):
        v = np.abs(pd.to_numeric(sub.get("Forward_Velocity"), errors="coerce").to_numpy())
        n = len(sub)
        total_path = np.nansum(v) / fps
        mean_speed = np.nanmean(v) if np.isfinite(v).any() else 0.0
        rows.append((*keys, n, n / fps, total_path, mean_speed))
    return pd.DataFrame(rows, columns=GROUP_KEYS +
                        ["n_frames", "duration_s", "total_path_mm", "mean_speed_mm_s"])


def filter_motile(df, fps=10.0, min_track_seconds=MIN_TRACK_SECONDS,
                  min_path_mm=MIN_PATH_MM, verbose=True):
    """Drop crops that are not live, moving worms.

    A crop is KEPT only if it was tracked for >= `min_track_seconds` AND its
    `total_path_mm` >= `min_path_mm`. This is the non-destructive, duration-aware
    analysis-time counterpart to the step-5 bubble filter: dead worms, debris and
    bubbles (near-zero path) and unusably short fragments are excluded from every
    downstream summary, but nothing is deleted on disk and the thresholds are
    tunable. Logs exactly what was dropped (never a silent cut).
    """
    if "Forward_Velocity" not in df.columns or df.empty:
        return df
    m = crop_motility(df, fps=fps)
    keep = (m.duration_s >= min_track_seconds) & (m.total_path_mm >= min_path_mm)
    kept_keys = set(map(tuple, m.loc[keep, GROUP_KEYS].to_numpy()))
    mask = df.set_index(GROUP_KEYS).index.isin(kept_keys)
    out = df[mask].reset_index(drop=True)
    if verbose:
        n_drop = (~keep).sum()
        too_short = (m.duration_s < min_track_seconds).sum()
        didnt_move = ((m.duration_s >= min_track_seconds) & (m.total_path_mm < min_path_mm)).sum()
        print(f"[motility QC] kept {keep.sum()}/{len(m)} crops "
              f"(dropped {n_drop}: {too_short} too short <{min_track_seconds}s, "
              f"{didnt_move} didn't move <{min_path_mm}mm); "
              f"{len(df) - len(out):,} of {len(df):,} frames removed")
    return out


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
    ap.add_argument("--keep_immotile", action="store_true",
                    help="disable the motility QC (by default only live worms that moved are analysed)")
    ap.add_argument("--min_track_seconds", type=float, default=MIN_TRACK_SECONDS,
                    help=f"motility QC: min tracked duration to keep a crop (default {MIN_TRACK_SECONDS})")
    ap.add_argument("--min_path_mm", type=float, default=MIN_PATH_MM,
                    help=f"motility QC: min total distance travelled to keep a crop (default {MIN_PATH_MM})")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_results(args.results, require_motile=not args.keep_immotile, fps=args.fps,
                      min_track_seconds=args.min_track_seconds, min_path_mm=args.min_path_mm)
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
