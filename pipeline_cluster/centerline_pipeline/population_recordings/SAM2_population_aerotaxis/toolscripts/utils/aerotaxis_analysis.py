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

# ----------------------------------------------------------------------------
# Aliveness QC (deliberately LENIENT) -- the goal is to keep every real worm,
# slow OR fast, and remove only inert objects (dead animals, bubbles, debris).
#
# A crop is kept if it was tracked long enough to trust AND shows ANY sign of
# life. "Sign of life" is a UNION of independent signals so a dwelling-but-alive
# worm (little net travel, but it still bends its body and occasionally reverses)
# is kept just like a fast roamer:
#   * it moved              -- integrated path OR net absolute displacement
#   * it changed posture    -- mean body-bend amplitude (Hilbert)
#   * it did something      -- >= 1 reversal or turn event
# Only a crop that is flat on ALL of these -- the definitive dead/bubble/debris
# signature -- is dropped. This is the non-destructive, duration-aware,
# analysis-time replacement for the irreversible step-5 bubble filter: it never
# deletes files, the thresholds are tunable, and every cut is logged with its
# reason. Because it is a union of cheap signals with small thresholds, it errs
# strongly toward keeping borderline crops (tighten only if you see junk).
#
# Thresholds are intentionally small; set require_alive=False to disable.
MIN_TRACK_SECONDS = 5.0    # a crop shorter than this (post-occlusion) is too brief to trust
MIN_PATH_MM = 0.3          # integrated |velocity| path above this = it moved
MIN_DISPLACEMENT_MM = 0.3  # net distance from the start position above this = it went somewhere
MIN_BEND_AMPLITUDE = 0.02  # mean Hilbert bend amplitude above this = it bent its body (alive)
MIN_EVENTS = 1             # >= this many reversal+turn onsets = it behaved


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------
def load_results(path, drop_occluded=True, require_alive=True, fps=10.0,
                 min_track_seconds=MIN_TRACK_SECONDS, min_path_mm=MIN_PATH_MM,
                 min_displacement_mm=MIN_DISPLACEMENT_MM,
                 min_bend_amplitude=MIN_BEND_AMPLITUDE, min_events=MIN_EVENTS,
                 require_motile=None, verbose=True):
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

    `require_alive` (default True): keep only crops that look like LIVE worms --
    tracked for at least `min_track_seconds` AND showing any sign of life
    (movement, body bends, or a behavioural event). This is a LENIENT union that
    keeps slow dwelling worms as readily as fast roamers and removes only inert
    dead/bubble/debris crops. Runs AFTER the occlusion filter, on real frames
    only. See `filter_alive`. Pass False to keep every crop.

    `require_motile` is the old name for `require_alive`; if given it wins (kept
    for backward compatibility).
    """
    if require_motile is not None:
        require_alive = require_motile
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
    if require_alive:
        df = filter_alive(df, fps=fps, min_track_seconds=min_track_seconds,
                          min_path_mm=min_path_mm, min_displacement_mm=min_displacement_mm,
                          min_bend_amplitude=min_bend_amplitude, min_events=min_events,
                          verbose=verbose)
    return df


def _apply_occlusion_filter(df, drop_occluded):
    """Drop occluded frames if requested and the `Occluded` column exists."""
    if drop_occluded and "Occluded" in df.columns:
        return df[df["Occluded"] == 0].reset_index(drop=True)
    return df


# ----------------------------------------------------------------------
# Aliveness QC -- keep every real worm (slow or fast), drop inert junk
# ----------------------------------------------------------------------
def _event_count(binary_series):
    """Number of 0->1 onsets in a per-frame 0/1 series (event count, not frames)."""
    a = pd.to_numeric(binary_series, errors="coerce").fillna(0).to_numpy() > 0.5
    return int(np.count_nonzero(a[1:] & ~a[:-1])) + int(a[:1].sum()) if len(a) else 0


def _nanmean(series):
    """nanmean that quietly returns NaN for an all-NaN/empty slice (no warning)."""
    a = pd.to_numeric(series, errors="coerce").to_numpy()
    return float(np.nanmean(a)) if np.isfinite(a).any() else np.nan


def crop_qc(df, fps=10.0):
    """Per-crop QC summary from the (already occlusion-filtered) table.

    One row per crop with the signals the aliveness gate uses, so you can eyeball
    the cropper's output and choose thresholds from data rather than by faith:
      n_frames, duration_s,
      total_path_mm       -- integral of |Forward_Velocity| (distance travelled),
      mean_speed_mm_s,
      net_displacement_mm -- max distance from the start position (needs X_mm/Y_mm),
      pos_spread_mm       -- sqrt(var(X)+var(Y)), the analysis-time analogue of the
                             bubble filter's positional SD (needs X_mm/Y_mm),
      mean_bend_amplitude, mean_bend_frequency_hz,
      n_events            -- reversal + turn onsets.
    Position-derived columns are NaN for tables without X_mm/Y_mm (older runs).
    """
    have_pos = {"X_mm", "Y_mm"}.issubset(df.columns)
    rows = []
    for keys, sub in df.groupby(GROUP_KEYS, sort=False):
        v = np.abs(pd.to_numeric(sub.get("Forward_Velocity"), errors="coerce").to_numpy())
        n = len(sub)
        total_path = np.nansum(v) / fps
        mean_speed = np.nanmean(v) if np.isfinite(v).any() else 0.0
        if have_pos:
            x = pd.to_numeric(sub["X_mm"], errors="coerce").to_numpy()
            y = pd.to_numeric(sub["Y_mm"], errors="coerce").to_numpy()
            ok = np.isfinite(x) & np.isfinite(y)
            if ok.any():
                x0, y0 = x[ok][0], y[ok][0]
                net_disp = float(np.nanmax(np.sqrt((x[ok] - x0) ** 2 + (y[ok] - y0) ** 2)))
                pos_spread = float(np.sqrt(np.nanvar(x[ok]) + np.nanvar(y[ok])))
            else:
                net_disp = pos_spread = np.nan
        else:
            net_disp = pos_spread = np.nan
        bend_amp = _nanmean(sub["Bend_Amplitude"]) if "Bend_Amplitude" in sub else np.nan
        bend_freq = _nanmean(sub["Bend_Frequency"]) if "Bend_Frequency" in sub else np.nan
        n_events = 0
        if "Reversal_Onset" in sub:
            n_events += int(pd.to_numeric(sub["Reversal_Onset"], errors="coerce").fillna(0).sum())
        elif "Reversal_Active" in sub:
            n_events += _event_count(sub["Reversal_Active"])
        if "Turn_Active" in sub:
            n_events += _event_count(sub["Turn_Active"])
        rows.append((*keys, n, n / fps, total_path, mean_speed, net_disp, pos_spread,
                     bend_amp, bend_freq, n_events))
    return pd.DataFrame(rows, columns=GROUP_KEYS + [
        "n_frames", "duration_s", "total_path_mm", "mean_speed_mm_s",
        "net_displacement_mm", "pos_spread_mm", "mean_bend_amplitude",
        "mean_bend_frequency_hz", "n_events"])


def filter_alive(df, fps=10.0, min_track_seconds=MIN_TRACK_SECONDS,
                 min_path_mm=MIN_PATH_MM, min_displacement_mm=MIN_DISPLACEMENT_MM,
                 min_bend_amplitude=MIN_BEND_AMPLITUDE, min_events=MIN_EVENTS,
                 verbose=True, return_qc=False):
    """Drop crops that show NO sign of life; keep every real worm, slow or fast.

    KEEP a crop iff it was tracked for >= `min_track_seconds` AND at least one
    life signal clears its (small) threshold:
        moved   : total_path_mm >= min_path_mm  OR  net_displacement_mm >= min_displacement_mm
        bent    : mean_bend_amplitude >= min_bend_amplitude
        behaved : n_events (reversal+turn onsets) >= min_events
    Only crops flat on ALL signals (dead / bubble / debris) are removed. This is
    a deliberately LENIENT union -- a dwelling worm that barely translocates but
    keeps bending is kept, and so is a fast roamer. Non-destructive (filters the
    loaded table, deletes nothing) and duration-aware. Logs what was dropped and
    why. Set `return_qc=True` to also get the per-crop QC table (with an `alive`
    column) for inspection.
    """
    if df.empty:
        return (df, crop_qc(df, fps=fps)) if return_qc else df
    m = crop_qc(df, fps=fps)
    long_enough = m.duration_s >= min_track_seconds
    moved = (m.total_path_mm >= min_path_mm) | (m.net_displacement_mm.fillna(-np.inf) >= min_displacement_mm)
    bent = m.mean_bend_amplitude.fillna(-np.inf) >= min_bend_amplitude
    behaved = m.n_events >= min_events
    alive = long_enough & (moved | bent | behaved)
    m = m.assign(alive=alive.to_numpy())

    kept_keys = set(map(tuple, m.loc[alive, GROUP_KEYS].to_numpy()))
    mask = df.set_index(GROUP_KEYS).index.isin(kept_keys)
    out = df[mask].reset_index(drop=True)
    if verbose:
        too_short = int((~long_enough).sum())
        inert = int((long_enough & ~(moved | bent | behaved)).sum())
        print(f"[aliveness QC] kept {int(alive.sum())}/{len(m)} crops "
              f"(dropped {int((~alive).sum())}: {too_short} too short <{min_track_seconds}s, "
              f"{inert} inert — no movement/bending/events); "
              f"{len(df) - len(out):,} of {len(df):,} frames removed")
    return (out, m) if return_qc else out


# Backward-compatible aliases (older code / notebooks used these names).
crop_motility = crop_qc
filter_motile = filter_alive


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
# Habituation / adaptation across successive gas pulses (uses Cycle_Index)
# ----------------------------------------------------------------------
def per_cycle_summary(df, feature="Forward_Velocity", state=None,
                      by=("Condition",), fps=10.0):
    """
    Mean `feature` per successive cycle, to test whether the O2 response
    habituates/adapts over repeated pulses.

    Uses the `Cycle_Index` column (0-based repeat number; -1 for baseline/pre/
    post) added by the extractor. Restrict to one phase with `state` (e.g.
    "21pct_O2" for the pulse response only). Returns a tidy frame
    [<by>, Cycle_Index, <feature>_mean, n_crops] — feed to seaborn.lineplot with
    x="Cycle_Index" to see the habituation curve.
    """
    if "Cycle_Index" not in df.columns:
        raise KeyError("Cycle_Index column required (re-run the extractor).")
    by = list(by)
    sub = df[df["Cycle_Index"] >= 0]
    if state is not None:
        sub = sub[sub["O2_State"] == state]
    if sub.empty:
        return pd.DataFrame(columns=by + ["Cycle_Index", f"{feature}_mean", "n_crops"])
    # crop-level mean first (so each worm contributes once per cycle), then group
    # mean. Dedupe keys so a `by` column that is also a GROUP_KEY (e.g. Condition)
    # is not listed twice.
    crop_keys = list(dict.fromkeys(by + ["Cycle_Index"] + GROUP_KEYS))
    per_crop = sub.groupby(crop_keys, observed=True)[feature].mean().reset_index()
    g = per_crop.groupby(by + ["Cycle_Index"], observed=True)
    out = g[feature].mean().reset_index().rename(columns={feature: f"{feature}_mean"})
    out["n_crops"] = g[GROUP_KEYS[-1]].nunique().values
    return out


# ----------------------------------------------------------------------
# Statistics: compare conditions per gas state, at the right replication unit
# ----------------------------------------------------------------------
def _crop_state_means(df, metric, state=None):
    """One `metric` value per crop (optionally within one O2_State).

    GROUP_KEYS already carries Condition/Recording/Crop_ID, so the grouped frame
    keeps everything the caller needs (Condition + the replication unit).
    """
    sub = df if state is None else df[df["O2_State"] == state]
    return sub.groupby(GROUP_KEYS, observed=True)[metric].mean().reset_index()


def compare_conditions_per_state(df, metric="Forward_Velocity",
                                 states=None, unit="Recording"):
    """
    Nonparametric comparison of `metric` across Conditions, within each gas
    state, at a sensible replication unit.

    Frames within a crop (and crops within a plate) are pseudo-replicates, so by
    default the metric is first averaged per crop, then per `unit` (Recording),
    and the test runs across those unit-level values — Kruskal–Wallis for >2
    Conditions, Mann–Whitney U for exactly 2. Returns a tidy table
    [O2_State, metric, test, statistic, p_value, n per condition]. Requires
    scipy; raises a clear error if it is unavailable.
    """
    try:
        from scipy import stats
    except ImportError as e:  # pragma: no cover
        raise ImportError("compare_conditions_per_state needs scipy "
                          "(conda/pip install scipy).") from e
    if states is None:
        states = [s for s in df["O2_State"].unique() if s not in ("pre_protocol", "post_protocol")]
    rows = []
    for state in states:
        cm = _crop_state_means(df, metric, state=state)
        # collapse crop -> unit (e.g. recording) means so replicates are independent
        unit_means = cm.groupby(["Condition", unit], observed=True)[metric].mean().reset_index()
        groups = [g[metric].dropna().to_numpy() for _, g in unit_means.groupby("Condition", observed=True)]
        groups = [g for g in groups if len(g) > 0]
        labels = [c for c, g in unit_means.groupby("Condition", observed=True) if len(g[metric].dropna())]
        n_by = {c: int(len(g[metric].dropna())) for c, g in unit_means.groupby("Condition", observed=True)}
        if len(groups) < 2 or all(len(g) < 2 for g in groups):
            rows.append(dict(O2_State=state, metric=metric, test="n/a",
                             statistic=np.nan, p_value=np.nan, n=n_by))
            continue
        if len(groups) == 2:
            stat, p = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
            test = f"Mann-Whitney U ({unit}-level)"
        else:
            stat, p = stats.kruskal(*groups)
            test = f"Kruskal-Wallis ({unit}-level)"
        rows.append(dict(O2_State=state, metric=metric, test=test,
                         statistic=float(stat), p_value=float(p), n=n_by))
    return pd.DataFrame(rows)


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
    ap.add_argument("--keep_all", "--keep_immotile", dest="keep_all", action="store_true",
                    help="disable the aliveness QC (by default only live worms are analysed)")
    ap.add_argument("--min_track_seconds", type=float, default=MIN_TRACK_SECONDS,
                    help=f"aliveness QC: min tracked duration to keep a crop (default {MIN_TRACK_SECONDS})")
    ap.add_argument("--min_path_mm", type=float, default=MIN_PATH_MM,
                    help=f"aliveness QC: min integrated path to count as 'moved' (default {MIN_PATH_MM})")
    ap.add_argument("--min_displacement_mm", type=float, default=MIN_DISPLACEMENT_MM,
                    help=f"aliveness QC: min net displacement to count as 'moved' (default {MIN_DISPLACEMENT_MM})")
    ap.add_argument("--min_bend_amplitude", type=float, default=MIN_BEND_AMPLITUDE,
                    help=f"aliveness QC: min mean bend amplitude to count as 'bent' (default {MIN_BEND_AMPLITUDE})")
    ap.add_argument("--min_events", type=int, default=MIN_EVENTS,
                    help=f"aliveness QC: min reversal+turn onsets to count as 'behaved' (default {MIN_EVENTS})")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Load raw (no aliveness filter yet) so we can WRITE the full per-crop QC
    # table, then apply the lenient gate. The QC CSV lets you eyeball the
    # cropper's output and retune thresholds without re-running the pipeline.
    raw = load_results(args.results, require_alive=False, fps=args.fps)
    _, qc = filter_alive(raw, fps=args.fps, min_track_seconds=args.min_track_seconds,
                         min_path_mm=args.min_path_mm, min_displacement_mm=args.min_displacement_mm,
                         min_bend_amplitude=args.min_bend_amplitude, min_events=args.min_events,
                         verbose=True, return_qc=True)
    qc.to_csv(outdir / "crop_qc.csv", index=False)
    df = raw if args.keep_all else raw[raw.set_index(GROUP_KEYS).index.isin(
        set(map(tuple, qc.loc[qc.alive, GROUP_KEYS].to_numpy())))].reset_index(drop=True)
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

    # habituation: mean feature per successive cycle (pulse phase if given)
    if "Cycle_Index" in df and (df["Cycle_Index"] >= 0).any():
        pc = per_cycle_summary(df, feature="Forward_Velocity",
                               state=args.pulse_state, fps=args.fps)
        pc.to_csv(outdir / "per_cycle_summary.csv", index=False)

    # statistics across conditions (only meaningful with >1 condition)
    if df["Condition"].nunique() > 1:
        stats_rows = []
        for metric in ["Forward_Velocity", "Reversal_Active", "Turn_Active", "Bend_Frequency"]:
            if metric in df and df[metric].notna().any():
                try:
                    stats_rows.append(compare_conditions_per_state(df, metric=metric))
                except ImportError:
                    print("[warn] scipy not available; skipping condition statistics")
                    stats_rows = []
                    break
        if stats_rows:
            stats_tbl = pd.concat(stats_rows, ignore_index=True)
            stats_tbl.to_csv(outdir / "condition_stats.csv", index=False)
            print("\nCondition comparison (Recording-level nonparametric tests):")
            print(stats_tbl.to_string(index=False))

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
