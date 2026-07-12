#!/usr/bin/env python3
"""
Extract temporal behavioural features for a single crop, aligned to a global
plate-level gas-shift protocol (aerotaxis / oxygen-sensing assays).

This REPLACES the spatial chemotaxis analysis. There are no gradients, no
radial distances and no chemotaxis index -- behaviour is described purely as
temporal state locked to global gas shifts (baseline O2, then repeating
pulse/return cycles).

Reads only artifacts already produced by the upstream (untouched) pipeline:
    reversal_annotation.csv          (annotate_reversals)          -> Reversal_Active, velocity sign
    turn_annotation_by_roundness.csv (calc_turns_by_roundness)     -> Turn_Active
    skeleton_spline_X/Y_coords_new.csv (process_skeleton_curvature)-> crop centroid
    track.txt                        (tracker stage log)           -> stage displacement

Output: a tidy, flat per-frame CSV with columns
    [Crop_ID, Frame, Time_Seconds, O2_State,
     Forward_Velocity, Reversal_Active, Turn_Active]

Downstream (create_results_dict_server.py) simply concatenates one of these
per crop into a single tidy table for Pandas / Seaborn / R.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# Protocol -> per-frame gas state
# ======================================================================
def build_o2_state(time_s, baseline_duration_s, baseline_state, cycle, n_cycles=None):
    """
    Map an array of timestamps (seconds) to gas states.

    Protocol = one baseline block, then `cycle` (an ordered list of
    {state, duration_s} phases) repeated. Fully vectorised and generic:
    any oxygen-sensing paradigm is expressed by editing baseline_* and cycle
    in config.yaml -- no code change needed here.
    """
    time_s = np.asarray(time_s, dtype=float)
    states = np.empty(time_s.shape, dtype=object)

    cycle_durations = np.array([float(p["duration_s"]) for p in cycle], dtype=float)
    cycle_states = [p["state"] for p in cycle]
    cycle_period = cycle_durations.sum()
    if cycle_period <= 0:
        raise ValueError("aerotaxis.cycle total duration must be > 0")
    phase_edges = np.cumsum(cycle_durations)  # boundaries within one cycle

    # baseline block
    in_baseline = time_s < baseline_duration_s
    states[in_baseline] = baseline_state

    # cyclic region
    t_cyc = time_s[~in_baseline] - baseline_duration_s
    cyc_index = np.floor(t_cyc / cycle_period).astype(int)
    t_in_cycle = t_cyc - cyc_index * cycle_period

    phase_idx = np.searchsorted(phase_edges, t_in_cycle, side="right")
    phase_idx = np.clip(phase_idx, 0, len(cycle_states) - 1)
    cyc_states = np.array([cycle_states[i] for i in phase_idx], dtype=object)

    if n_cycles is not None:
        cyc_states[cyc_index >= n_cycles] = "post_protocol"

    states[~in_baseline] = cyc_states
    return states


# ======================================================================
# Loaders (formats verified against the upstream writers)
# ======================================================================
def load_reversal(path):
    """reversal_annotation.csv: index + 1 data column of {-1, 0, 1}."""
    df = pd.read_csv(path, index_col=0)
    return df.iloc[:, 0].to_numpy()


def load_turn(path):
    """turn_annotation_by_roundness.csv: has a binary 'turn' column."""
    df = pd.read_csv(path, index_col=0)
    return df["turn"].to_numpy()


def load_centroid_px(x_path, y_path):
    """Skeleton spline coords (header=None, index=None) -> per-frame centroid (px)."""
    xs = pd.read_csv(x_path, header=None)
    ys = pd.read_csv(y_path, header=None)
    cx = xs.mean(axis=1, skipna=True).to_numpy()
    cy = ys.mean(axis=1, skipna=True).to_numpy()
    return cx, cy


def _fit_length(arr, n):
    """Truncate or NaN-pad a 1-D array to length n so all features align on Frame."""
    arr = np.asarray(arr, dtype=float)
    if len(arr) >= n:
        return arr[:n]
    out = np.full(n, np.nan)
    out[: len(arr)] = arr
    return out


# ======================================================================
# Forward velocity
# ======================================================================
# ----------------------------------------------------------------------
# TODO(track.txt): DEFERRED until the cropper settings are finalised.
#
# The magnitude of Forward_Velocity depends on how the tracker's stage log
# (track.txt) encodes position -- column layout and units (px vs mm) are
# setup-specific and not yet known. Everything else in this file is final.
#
# When a viable crop exists, replace ONLY the body of load_stage_px() below
# with the real column names / units. Nothing else in the pipeline touches
# velocity. Until then we fall back to crop-centroid-only speed (stage drift
# ignored) and emit a warning, so the pipeline runs end-to-end today.
# ----------------------------------------------------------------------
def load_stage_px(track_txt, n_frames):
    """
    Stage/table position per frame from track.txt, in the SAME px units as the
    crop centroid. Returns (sx, sy), or zeros (+warning) if unavailable.

    PLACEHOLDER heuristic: parse tolerantly and take the last two numeric
    columns as stage X, Y. Verify against a real track.txt before trusting the
    velocity magnitude (see TODO above).
    """
    p = Path(track_txt)
    if not p.exists():
        print(f"[warn] {track_txt} not found -- crop-centroid speed only "
              f"(stage drift ignored).", file=sys.stderr)
        return np.zeros(n_frames), np.zeros(n_frames)
    try:
        raw = pd.read_csv(p, sep=None, engine="python", header=None, comment="#")
        num = raw.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
        if num.shape[1] < 2:
            raise ValueError("fewer than 2 numeric columns")
        sx = num.iloc[:, -2].to_numpy(dtype=float)
        sy = num.iloc[:, -1].to_numpy(dtype=float)
        return sx, sy
    except Exception as e:  # noqa: BLE001 -- tolerant by design (placeholder)
        print(f"[warn] could not parse {track_txt} ({e}); crop-centroid speed only.",
              file=sys.stderr)
        return np.zeros(n_frames), np.zeros(n_frames)


def compute_forward_velocity(cx, cy, sx, sy, reversal_active, fps, factor_px_to_mm, smooth_win):
    """
    Signed forward velocity (mm/s): speed magnitude signed by reversal state
    (forward -> positive, reversal -> negative). Position is smoothed before
    differentiating to suppress tracking jitter.
    """
    abs_x_mm = (sx + cx) * factor_px_to_mm
    abs_y_mm = (sy + cy) * factor_px_to_mm
    abs_x_mm = pd.Series(abs_x_mm).rolling(smooth_win, min_periods=1, center=True).mean().to_numpy()
    abs_y_mm = pd.Series(abs_y_mm).rolling(smooth_win, min_periods=1, center=True).mean().to_numpy()
    speed = np.sqrt(np.gradient(abs_x_mm) ** 2 + np.gradient(abs_y_mm) ** 2) * fps  # mm/s
    direction = np.where(reversal_active == 1, -1.0, 1.0)
    return speed * direction


# ======================================================================
def main(arg_list=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crop_id", required=True, help="Crop_ID (the track_dir name)")
    ap.add_argument("--reversal_annotation", required=True)
    ap.add_argument("--turn_annotation", required=True)
    ap.add_argument("--skeleton_x", required=True)
    ap.add_argument("--skeleton_y", required=True)
    ap.add_argument("--worm_pos", required=True, help="track.txt stage log")
    ap.add_argument("--fps", type=float, required=True)
    ap.add_argument("--factor_px_to_mm", type=float, required=True)
    ap.add_argument("--speed_smooth_window", type=int, default=None,
                    help="rolling window (frames) for position smoothing; default = round(fps)")
    # protocol timing
    ap.add_argument("--t0_offset_s", type=float, default=0.0)
    ap.add_argument("--baseline_duration_s", type=float, required=True)
    ap.add_argument("--baseline_state", required=True)
    ap.add_argument("--cycle_json", required=True,
                    help='JSON list of {"state","duration_s"} phases')
    ap.add_argument("--n_cycles", default="none")
    # output
    ap.add_argument("--out_csv", required=True)
    args = ap.parse_args(arg_list)

    cycle = json.loads(args.cycle_json)
    n_cycles = None if str(args.n_cycles).lower() in ("none", "null", "") else int(args.n_cycles)
    smooth_win = args.speed_smooth_window or max(1, int(round(args.fps)))

    # ---- load per-frame features ----
    reversal = load_reversal(args.reversal_annotation)
    turn = load_turn(args.turn_annotation)
    cx, cy = load_centroid_px(args.skeleton_x, args.skeleton_y)

    n = min(len(reversal), len(turn), len(cx), len(cy))
    if n == 0:
        raise ValueError(f"[{args.crop_id}] no frames to process (empty inputs).")

    reversal = _fit_length(reversal, n)
    turn = _fit_length(turn, n)
    cx, cy = _fit_length(cx, n), _fit_length(cy, n)
    sx, sy = load_stage_px(args.worm_pos, n)
    sx, sy = _fit_length(sx, n), _fit_length(sy, n)

    reversal_active = (reversal == -1).astype(int)
    forward_velocity = compute_forward_velocity(
        cx, cy, sx, sy, reversal_active, args.fps, args.factor_px_to_mm, smooth_win
    )

    # ---- time + gas state ----
    frame = np.arange(n)
    time_s = args.t0_offset_s + frame / args.fps
    o2_state = build_o2_state(
        time_s, args.baseline_duration_s, args.baseline_state, cycle, n_cycles
    )

    # ---- tidy output ----
    out = pd.DataFrame({
        "Crop_ID": args.crop_id,
        "Frame": frame,
        "Time_Seconds": time_s,
        "O2_State": o2_state,
        "Forward_Velocity": forward_velocity,
        "Reversal_Active": reversal_active,
        "Turn_Active": turn.astype(int),
    })
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print(f"[{args.crop_id}] wrote {len(out)} frames -> {args.out_csv}")


if __name__ == "__main__":
    main(sys.argv[1:])
